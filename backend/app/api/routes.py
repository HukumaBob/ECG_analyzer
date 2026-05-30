"""
API-маршруты.

POST /analyze  — принимает файл ЭКГ и возвращает диагностическое заключение
GET  /health   — статус сервиса и состояние модели
"""

import json
import uuid
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

import numpy as np

from app.schemas import AnalyzeResponse, EcgPreview, HealthResponse, PatientMetadataRequest
from app.services.loader import ModelLoader
from app.services.preprocessor import load_and_segment
from app.services.inference import run_inference
from app.services.aggregator import aggregate
from app.services.report import build_diagnoses, build_conclusion, check_poor_quality
from app.services.bayes import apply_bayes, PatientMetadata

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


@router.get("/health", response_model=HealthResponse, summary="Статус сервиса")
async def health() -> HealthResponse:
    loader = ModelLoader.get_instance()
    device_str = str(loader.device) if loader.is_loaded else None
    return HealthResponse(
        status="ok" if loader.is_loaded else "degraded",
        model_loaded=loader.is_loaded,
        device=device_str,
    )


# ---------------------------------------------------------------------------
# POST /analyze
# ---------------------------------------------------------------------------


ALLOWED_EXTENSIONS = {".hea", ".dat", ".mat", ".csv"}

# Превью: показываем до N первых сегментов, downsampled до PREVIEW_FS
PREVIEW_SEGMENTS = 2   # до 10 сек
PREVIEW_FS = 100       # 100 Гц → 500 точек на сегмент; JSON < 100 КБ


def _build_preview(segments: np.ndarray, source_fs: int = 500) -> EcgPreview:
    """Формирует объект превью из массива сегментов [N, 12, 2500]."""
    n_show = min(PREVIEW_SEGMENTS, len(segments))
    # Склеиваем нужные сегменты → [12, T]
    signal = np.concatenate([segments[i] for i in range(n_show)], axis=1)  # [12, T]

    # Downsample: берём каждый k-й отсчёт (простой decimation без фильтра,
    # сигнал уже прошёл через модель — артефакты aliasing здесь не критичны)
    step = source_fs // PREVIEW_FS
    signal_ds = signal[:, ::step]  # [12, T//step]

    duration = signal.shape[1] / source_fs
    leads_list = [row.round(5).tolist() for row in signal_ds]

    return EcgPreview(
        leads=leads_list,
        sample_rate=PREVIEW_FS,
        duration_sec=round(duration, 2),
    )
MAX_FILE_SIZE_MB = 50


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Анализ ЭКГ",
    description=(
        "Принимает файл(ы) ЭКГ (WFDB .hea+.dat, MATLAB .mat, CSV). "
        "Для WFDB передайте оба файла (.hea и .dat) одновременно. "
        "**Не является медицинским диагностическим заключением.**"
    ),
)
async def analyze(
    files: Annotated[list[UploadFile], File(description="Файл(ы) ЭКГ. Для WFDB — .hea и .dat вместе.")],
    patient_id: Annotated[Optional[str], Form()] = None,
    notes: Annotated[Optional[str], Form()] = None,
    metadata_json: Annotated[Optional[str], Form(
        description="JSON с клиническими метаданными (PatientMetadataRequest). Опционально."
    )] = None,
) -> AnalyzeResponse:
    loader = ModelLoader.get_instance()
    if not loader.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Модель не загружена. Сервис недоступен.",
        )

    if not files:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Файл не передан.")

    # Читаем все файлы, проверяем расширения и суммарный размер
    file_map: dict[str, bytes] = {}  # filename → bytes
    total_size = 0
    for upload in files:
        fname = upload.filename or ""
        suffix = "." + fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Неподдерживаемый формат файла: '{suffix}'. Допустимые: {sorted(ALLOWED_EXTENSIONS)}",
            )
        data = await upload.read()
        total_size += len(data)
        if total_size / (1024 * 1024) > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Файлы слишком большие (суммарно > {MAX_FILE_SIZE_MB} МБ).",
            )
        file_map[fname] = data

    # Определяем «главный» файл: для WFDB — .hea, иначе единственный файл
    hea_files = [n for n in file_map if n.lower().endswith(".hea")]
    if hea_files:
        filename = hea_files[0]
    elif len(file_map) == 1:
        filename = next(iter(file_map))
    else:
        # Несколько файлов, но нет .hea — ошибка
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Передано несколько файлов без .hea. Для WFDB загрузите .hea и .dat вместе.",
        )

    contents = file_map[filename]
    size_mb = total_size / (1024 * 1024)

    # Разбор клинических метаданных
    patient_meta: Optional[PatientMetadata] = None
    if metadata_json:
        try:
            meta_req = PatientMetadataRequest.model_validate(json.loads(metadata_json))
            patient_meta = PatientMetadata(
                age=meta_req.age,
                sex=meta_req.sex,
                medications=meta_req.medications,
                icd10_codes=meta_req.icd10_codes,
                heart_rate=meta_req.heart_rate,
                potassium=meta_req.potassium,
                magnesium=meta_req.magnesium,
                has_pacemaker=meta_req.has_pacemaker,
            )
        except (json.JSONDecodeError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Неверный формат metadata_json: {exc}",
            )

    request_id = str(uuid.uuid4())
    logger.info(
        "Запрос %s: файл=%s size=%.2f МБ patient_id=%s meta=%s",
        request_id, filename, size_mb, patient_id,
        "yes" if patient_meta else "no",
    )

    # --- Pipeline ---
    extra_files = {k: v for k, v in file_map.items() if k != filename}
    try:
        segments = load_and_segment(contents, filename, extra_files=extra_files)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    try:
        probs_per_segment = run_inference(segments)
    except Exception as exc:
        logger.exception("Inference error in request %s", request_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка inference: {exc}")

    agg = aggregate(probs_per_segment)
    raw_probs = agg["max"]                          # [17] — до поправки
    final_probs = apply_bayes(raw_probs, patient_meta)  # [17] — после поправки

    diagnoses = build_diagnoses(final_probs)
    poor_quality = check_poor_quality(diagnoses)
    conclusion = build_conclusion(diagnoses, poor_quality)
    has_critical = any(d.triggered and d.label in {"ventricular_tachycardia", "infarction"} for d in diagnoses)

    try:
        ecg_preview = _build_preview(segments)
    except Exception:
        logger.warning("Не удалось сформировать ecg_preview для запроса %s", request_id)
        ecg_preview = None

    return AnalyzeResponse(
        request_id=request_id,
        has_critical=has_critical,
        diagnoses=diagnoses,
        conclusion=conclusion,
        segments_analyzed=len(segments),
        device_used=str(loader.device),
        warning="Низкое качество сигнала: достоверность снижена." if poor_quality else None,
        ecg_preview=ecg_preview,
    )
