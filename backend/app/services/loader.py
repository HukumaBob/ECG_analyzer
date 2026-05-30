"""
Singleton загрузчика модели ECG-FM.

Чекпойнт: /mnt/work-disk/Documents/Dev/ECG-FM/ckpts/mimic_iv_ecg_finetuned.pt
Конфиг:    /mnt/work-disk/Documents/Dev/ECG-FM/ckpts/mimic_iv_ecg_finetuned.yaml

Модель загружается через fairseq-signals (editable install обязателен).
"""

import logging
import threading
from pathlib import Path
from typing import Optional

import torch

logger = logging.getLogger(__name__)

CHECKPOINT_PATH = Path("/mnt/work-disk/Documents/Dev/ECG-FM/ckpts/mimic_iv_ecg_finetuned.pt")
CONFIG_PATH = Path("/mnt/work-disk/Documents/Dev/ECG-FM/ckpts/mimic_iv_ecg_finetuned.yaml")

# 17 классов в том порядке, в котором их возвращает модель
CLASS_LABELS: list[str] = [
    "poor_data_quality",
    "sinus_rhythm",
    "pvc",
    "tachycardia",
    "ventricular_tachycardia",
    "svt_with_aberrancy",
    "atrial_fibrillation",
    "atrial_flutter",
    "bradycardia",
    "accessory_pathway_wpw",
    "av_block_2_3",
    "av_block_1",
    "bifascicular_block",
    "rbbb",
    "lbbb",
    "infarction",
    "electronic_pacemaker",
]

CRITICAL_CLASSES: frozenset[str] = frozenset(["ventricular_tachycardia", "infarction"])


class ModelLoader:
    """Thread-safe singleton для загрузки и хранения модели ECG-FM."""

    _instance: Optional["ModelLoader"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._model = None
        self._device: Optional[torch.device] = None
        self._loaded = False

    @classmethod
    def get_instance(cls) -> "ModelLoader":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Загружает модель с диска. Повторный вызов — no-op."""
        if self._loaded:
            return

        if not CHECKPOINT_PATH.exists():
            raise FileNotFoundError(f"Чекпойнт не найден: {CHECKPOINT_PATH}")
        if not CONFIG_PATH.exists():
            raise FileNotFoundError(f"Конфиг не найден: {CONFIG_PATH}")

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Устройство inference: %s", self._device)

        self._model = self._load_fairseq_model()
        self._model.eval()
        self._loaded = True
        logger.info("Модель ECG-FM готова (device=%s)", self._device)

    def unload(self) -> None:
        """Освобождает модель из памяти."""
        self._model = None
        self._loaded = False
        if self._device and self._device.type == "cuda":
            torch.cuda.empty_cache()
        logger.info("Модель выгружена.")

    @property
    def model(self):
        if not self._loaded or self._model is None:
            raise RuntimeError("Модель не загружена. Вызовите load() сначала.")
        return self._model

    @property
    def device(self) -> torch.device:
        if self._device is None:
            raise RuntimeError("Модель не загружена.")
        return self._device

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_fairseq_model(self):
        """
        Загружает модель через fairseq-signals.
        fairseq-signals должен быть установлен как editable install.
        """
        try:
            from fairseq_signals.utils import checkpoint_utils  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "fairseq-signals не найден. "
                "Установите: uv pip install -e /mnt/work-disk/Documents/Dev/fairseq-signals/"
            ) from exc

        # no_pretrained_weights=True: пропускаем загрузку pretrain-чекпойнта с кластера,
        # веса энкодера уже встроены в finetuned .pt
        model, _cfg, _task = checkpoint_utils.load_model_and_task(
            str(CHECKPOINT_PATH),
            model_overrides={"no_pretrained_weights": True},
        )
        model = model.to(self._device)
        return model
