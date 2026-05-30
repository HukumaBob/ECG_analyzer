"""
Предобработка ЭКГ-сигналов.

Поддерживаемые форматы:
  - WFDB (.hea + .dat) — через wfdb
  - MATLAB (.mat)      — через scipy.io
  - CSV (.csv)         — через pandas

Pipeline для каждого формата:
  1. Чтение → numpy array [leads, samples]
  2. Проверка 12 каналов
  3. Ресемплинг → 500 Hz
  4. Нарезка на 5-сек сегменты [N, 12, 2500]
"""

import io
import logging
import tempfile
from pathlib import Path

import numpy as np
import scipy.io
import scipy.signal
import wfdb

logger = logging.getLogger(__name__)

TARGET_FS = 500        # Hz — требование ECG-FM
SEGMENT_SECONDS = 5    # длина сегмента
SEGMENT_SAMPLES = TARGET_FS * SEGMENT_SECONDS   # 2500 отсчётов
MIN_SEGMENTS = 1       # минимум 1 сегмент (≥ 5 сек; хватает для диагностики)
N_LEADS = 12


# ---------------------------------------------------------------------------
# Публичный интерфейс
# ---------------------------------------------------------------------------


def load_and_segment(file_bytes: bytes, filename: str, extra_files: dict[str, bytes] | None = None) -> np.ndarray:
    """
    Читает файл ЭКГ, ресемплирует до 500 Hz и нарезает на сегменты.

    Parameters
    ----------
    file_bytes : bytes
        Содержимое основного файла.
    filename : str
        Имя основного файла (используется для определения формата).
    extra_files : dict[str, bytes] | None
        Дополнительные файлы, необходимые для чтения (напр. .dat для WFDB).

    Returns
    -------
    segments : np.ndarray
        shape [N, 12, 2500], float32
    """
    suffix = _get_suffix(filename)
    signal, fs = _read_signal(file_bytes, filename, suffix, extra_files=extra_files or {})

    _validate_leads(signal, filename)

    if fs != TARGET_FS:
        signal = _resample(signal, fs, TARGET_FS)

    segments = _segment(signal)

    if len(segments) < MIN_SEGMENTS:
        raise ValueError(
            f"Запись слишком короткая: менее 2 секунд. "
            f"Минимальная длина для анализа — 2 сек."
        )

    logger.info("Preprocessed '%s': fs_in=%d → %d Hz, %d segments", filename, fs, TARGET_FS, len(segments))
    return segments.astype(np.float32)


# ---------------------------------------------------------------------------
# Чтение форматов
# ---------------------------------------------------------------------------


def _get_suffix(filename: str) -> str:
    return Path(filename).suffix.lower()


def _read_signal(file_bytes: bytes, filename: str, suffix: str, extra_files: dict[str, bytes] | None = None) -> tuple[np.ndarray, int]:
    """
    Returns signal [leads, samples] и частоту дискретизации.
    """
    if suffix == ".mat":
        return _read_mat(file_bytes)
    elif suffix == ".csv":
        return _read_csv(file_bytes)
    elif suffix in (".hea", ".dat"):
        return _read_wfdb(file_bytes, filename, suffix, extra_files=extra_files or {})
    else:
        raise ValueError(f"Неподдерживаемый формат: '{suffix}'")


def _read_mat(file_bytes: bytes) -> tuple[np.ndarray, int]:
    """MATLAB .mat — формат MIMIC-IV-ECG (CODE-15)."""
    try:
        buf = io.BytesIO(file_bytes)
        mat = scipy.io.loadmat(buf)
    except Exception as exc:
        raise ValueError(f"Не удалось прочитать .mat файл: {exc}") from exc

    # Разные датасеты хранят ЭКГ под разными именами
    for key in ("val", "feats", "signal", "ecg", "data"):
        if key in mat:
            signal = mat[key]
            break
    else:
        candidate_keys = [k for k in mat if not k.startswith("_")]
        if len(candidate_keys) == 1:
            signal = mat[candidate_keys[0]]
        else:
            raise ValueError(
                f"Не найдено поле с ЭКГ-данными в .mat файле. Доступные ключи: {candidate_keys}"
            )

    signal = np.array(signal, dtype=float)
    if signal.ndim != 2:
        raise ValueError(f"Ожидался 2D массив в .mat, получен: {signal.shape}")

    # Привести к [leads, samples]
    if signal.shape[0] > signal.shape[1]:
        signal = signal.T

    # Частота: ищем в mat, по умолчанию — 500
    # Поддерживаем curr_sample_rate (fairseq-signals) и стандартные имена
    for fs_key in ("curr_sample_rate", "fs", "Fs", "fs_Hz", "sample_rate"):
        if fs_key in mat:
            fs = int(np.array(mat[fs_key]).flat[0])
            break
    else:
        fs = 500
    return signal, fs


def _read_csv(file_bytes: bytes) -> tuple[np.ndarray, int]:
    """
    CSV: либо 12 колонок (отведения) × N строк (отсчёты),
    либо заголовок с именами отведений, либо колонка 'fs'.
    """
    import pandas as pd  # noqa: PLC0415

    try:
        buf = io.StringIO(file_bytes.decode("utf-8", errors="replace"))
        df = pd.read_csv(buf)
    except Exception as exc:
        raise ValueError(f"Не удалось прочитать .csv файл: {exc}") from exc

    # Извлечь fs из отдельной строки/колонки, если есть
    fs = 500
    if "fs" in df.columns:
        fs = int(df["fs"].iloc[0])
        df = df.drop(columns=["fs"])
    elif "Fs" in df.columns:
        fs = int(df["Fs"].iloc[0])
        df = df.drop(columns=["Fs"])

    signal = df.select_dtypes(include=[np.number]).values.T  # [leads, samples]
    if signal.shape[0] > signal.shape[1]:
        signal = signal.T

    return signal, fs


def _read_wfdb(file_bytes: bytes, filename: str, suffix: str, extra_files: dict[str, bytes] | None = None) -> tuple[np.ndarray, int]:
    """
    WFDB требует пару .hea + .dat.
    Записываем все переданные файлы во временную директорию.
    """
    extra_files = extra_files or {}
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Записываем основной файл
            (tmpdir_path / Path(filename).name).write_bytes(file_bytes)

            # Записываем дополнительные файлы (.dat и др.) в ту же папку
            for extra_name, extra_bytes in extra_files.items():
                (tmpdir_path / Path(extra_name).name).write_bytes(extra_bytes)

            # .hea всегда должен быть — ищем его в tmpdir
            hea_files = list(tmpdir_path.glob("*.hea"))
            if not hea_files:
                raise ValueError("Файл .hea не найден. Передайте .hea и .dat вместе.")

            record_name = str(hea_files[0].with_suffix(""))
            record = wfdb.rdrecord(record_name)
            signal = record.p_signal.T  # [leads, samples]
            fs = record.fs
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            f"Не удалось прочитать WFDB-файл '{filename}': {exc}."
        ) from exc

    return signal, fs


# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------


def _validate_leads(signal: np.ndarray, filename: str) -> None:
    if signal.ndim != 2:
        raise ValueError(f"Ожидался 2D массив [leads, samples], получен: {signal.shape}")
    n_leads = signal.shape[0]
    if n_leads != N_LEADS:
        raise ValueError(
            f"Ожидается 12 отведений, в файле '{filename}' найдено {n_leads}."
        )


def _resample(signal: np.ndarray, fs_in: int, fs_out: int) -> np.ndarray:
    """Ресемплинг каждого отведения через scipy.signal.resample_poly."""
    from math import gcd  # noqa: PLC0415

    g = gcd(fs_out, fs_in)
    up, down = fs_out // g, fs_in // g
    resampled = np.stack(
        [scipy.signal.resample_poly(ch, up, down) for ch in signal]
    )
    return resampled


def _segment(signal: np.ndarray) -> np.ndarray:
    """
    Нарезает [12, T] на [N, 12, 2500] без перекрытия.
    Хвост дополняется нулями (zero-pad) если он >= 2 сек (1000 отсчётов);
    слишком короткие хвосты (<2 сек) отбрасываются.
    """
    n_leads, total = signal.shape
    n_full = total // SEGMENT_SAMPLES
    segments = []
    for i in range(n_full):
        start = i * SEGMENT_SAMPLES
        segments.append(signal[:, start : start + SEGMENT_SAMPLES])

    # Хвост: дополняем нулями если длина >= 2 сек
    tail_start = n_full * SEGMENT_SAMPLES
    tail = signal[:, tail_start:]
    MIN_TAIL_SAMPLES = TARGET_FS * 2  # 1000 отсчётов = 2 сек
    if tail.shape[1] >= MIN_TAIL_SAMPLES:
        pad = np.zeros((n_leads, SEGMENT_SAMPLES - tail.shape[1]), dtype=signal.dtype)
        segments.append(np.concatenate([tail, pad], axis=1))

    return np.stack(segments) if segments else np.empty((0, N_LEADS, SEGMENT_SAMPLES), dtype=np.float32)
