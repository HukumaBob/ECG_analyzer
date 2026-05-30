"""
Байесовская поправка вероятностей на клинические метаданные.

Алгоритм: таблица prior-смещений (log-odds additive).

Формула для каждого класса i:
    log_odds(P) = log(P / (1 - P))
    log_odds'   = log_odds(P) + delta_i
    P'          = sigmoid(log_odds')

delta_i > 0 → повышаем вероятность класса i
delta_i < 0 → понижаем

Если метаданные не переданы — возвращаем исходный вектор без изменений.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np

# ---------------------------------------------------------------------------
# Индексы классов (совпадают с CLASS_META в report.py)
# ---------------------------------------------------------------------------

IDX = {
    "poor_data_quality":      0,
    "sinus_rhythm":           1,
    "pvc":                    2,
    "tachycardia":            3,
    "ventricular_tachycardia":4,
    "svt_with_aberrancy":     5,
    "atrial_fibrillation":    6,
    "atrial_flutter":         7,
    "bradycardia":            8,
    "accessory_pathway_wpw":  9,
    "av_block_2_3":          10,
    "av_block_1":            11,
    "bifascicular_block":    12,
    "rbbb":                  13,
    "lbbb":                  14,
    "infarction":            15,
    "electronic_pacemaker":  16,
}

# ---------------------------------------------------------------------------
# Таблица prior-смещений
# Каждый элемент: (condition_fn, {label: delta})
# condition_fn принимает PatientMetadata и возвращает bool
# ---------------------------------------------------------------------------

# Входные метаданные — простой dataclass, не Pydantic
# (чтобы не создавать лишнюю зависимость внутри сервиса)
from dataclasses import dataclass, field


@dataclass
class PatientMetadata:
    age: Optional[int] = None                  # лет
    sex: Optional[str] = None                  # "M" | "F"
    medications: list[str] = field(default_factory=list)
    # МКБ-10 диагнозы в виде кодов или текста
    icd10_codes: list[str] = field(default_factory=list)
    heart_rate: Optional[int] = None           # уд/мин из анамнеза
    potassium: Optional[float] = None          # K+, ммоль/л
    magnesium: Optional[float] = None          # Mg²+, ммоль/л
    has_pacemaker: Optional[bool] = None       # известный ЭКС


# ---------------------------------------------------------------------------
# Правила
# ---------------------------------------------------------------------------

def _has_med(meta: PatientMetadata, *keywords: str) -> bool:
    meds = [m.lower() for m in meta.medications]
    return any(kw in m for kw in keywords for m in meds)


def _has_icd(meta: PatientMetadata, *prefixes: str) -> bool:
    codes = [c.upper() for c in meta.icd10_codes]
    return any(c.startswith(p.upper()) for p in prefixes for c in codes)


# Список правил: (condition, {class_label: log_odds_delta})
# Смещения подобраны экспертно (умеренные ±0.5 / сильные ±1.0)
_RULES: list[tuple] = [
    # --- Возраст > 70 ---
    (
        lambda m: m.age is not None and m.age > 70,
        {
            "av_block_1":       +0.5,
            "av_block_2_3":     +0.5,
            "bifascicular_block": +0.5,
            "rbbb":             +0.3,
            "lbbb":             +0.3,
            "atrial_fibrillation": +0.5,
        },
    ),
    # --- Возраст < 40 (ДПП и WPW чаще) ---
    (
        lambda m: m.age is not None and m.age < 40,
        {
            "accessory_pathway_wpw": +0.4,
            "svt_with_aberrancy":    +0.3,
        },
    ),
    # --- Дигиталис ---
    (
        lambda m: _has_med(m, "digoxin", "digitalis", "дигоксин", "дигиталис"),
        {
            "av_block_1":   +0.6,
            "av_block_2_3": +0.5,
            "bradycardia":  +0.5,
            "pvc":          +0.4,
        },
    ),
    # --- Антиаритмики класса I/III (амиодарон, флекаинид и др.) ---
    (
        lambda m: _has_med(m, "amiodarone", "амиодарон", "flecainide", "флекаинид",
                            "sotalol", "соталол", "propafenone", "пропафенон"),
        {
            "bradycardia":  +0.5,
            "av_block_1":   +0.4,
            "av_block_2_3": +0.3,
            "lbbb":         +0.3,   # лекарственная блокада
        },
    ),
    # --- β-блокаторы ---
    (
        lambda m: _has_med(m, "bisoprolol", "бисопролол", "metoprolol", "метопролол",
                            "atenolol", "атенолол", "carvedilol", "карведилол",
                            "propranolol", "пропранолол"),
        {
            "bradycardia":  +0.6,
            "av_block_1":   +0.3,
        },
    ),
    # --- Известная ФП в анамнезе (МКБ I48) ---
    (
        lambda m: _has_icd(m, "I48"),
        {
            "atrial_fibrillation": +1.0,
            "atrial_flutter":      +0.3,
        },
    ),
    # --- Известная ИБС/инфаркт в анамнезе (МКБ I20-I25) ---
    (
        lambda m: _has_icd(m, "I20", "I21", "I22", "I23", "I24", "I25"),
        {
            "infarction":     +0.8,
            "lbbb":           +0.4,
            "bifascicular_block": +0.3,
        },
    ),
    # --- Известная СН/кардиомиопатия (МКБ I42, I50) ---
    (
        lambda m: _has_icd(m, "I42", "I50"),
        {
            "lbbb":                  +0.5,
            "ventricular_tachycardia": +0.4,
            "atrial_fibrillation":   +0.4,
        },
    ),
    # --- Установленный кардиостимулятор ---
    (
        lambda m: m.has_pacemaker is True or _has_icd(m, "Z95.0", "Z950"),
        {
            "electronic_pacemaker": +2.0,
            "sinus_rhythm":         -1.0,  # ритм ЭКС вытесняет синусовый
        },
    ),
    # --- Гипокалиемия (K+ < 3.5) ---
    (
        lambda m: m.potassium is not None and m.potassium < 3.5,
        {
            "pvc":                   +0.5,
            "ventricular_tachycardia": +0.4,
            "atrial_fibrillation":   +0.3,
        },
    ),
    # --- Гипомагниемия (Mg²+ < 0.7) ---
    (
        lambda m: m.magnesium is not None and m.magnesium < 0.7,
        {
            "pvc":                   +0.4,
            "ventricular_tachycardia": +0.3,
        },
    ),
    # --- Тахикардия из анамнеза (ЧСС > 100) ---
    (
        lambda m: m.heart_rate is not None and m.heart_rate > 100,
        {
            "tachycardia":           +0.8,
            "atrial_fibrillation":   +0.3,
            "svt_with_aberrancy":    +0.2,
            "ventricular_tachycardia": +0.2,
        },
    ),
    # --- Брадикардия из анамнеза (ЧСС < 50) ---
    (
        lambda m: m.heart_rate is not None and m.heart_rate < 50,
        {
            "bradycardia":  +0.8,
            "av_block_2_3": +0.3,
        },
    ),
]


# ---------------------------------------------------------------------------
# Публичный интерфейс
# ---------------------------------------------------------------------------

def apply_bayes(probs: np.ndarray, meta: Optional[PatientMetadata]) -> np.ndarray:
    """
    Применяет байесовскую поправку к вектору вероятностей [17].

    Parameters
    ----------
    probs : np.ndarray
        shape [17], float32 — исходные вероятности от модели
    meta : PatientMetadata | None
        Клинические метаданные. None → вернуть probs без изменений.

    Returns
    -------
    np.ndarray
        shape [17], float32 — скорректированные вероятности
    """
    if meta is None:
        return probs

    log_odds = _to_log_odds(probs.astype(np.float64))

    for condition, deltas in _RULES:
        try:
            if condition(meta):
                for label, delta in deltas.items():
                    log_odds[IDX[label]] += delta
        except Exception:
            # Правило не должно ронять pipeline
            pass

    return _from_log_odds(log_odds).astype(np.float32)


# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------

_EPS = 1e-7   # защита от log(0)


def _to_log_odds(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, _EPS, 1.0 - _EPS)
    return np.log(p / (1.0 - p))


def _from_log_odds(lo: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-lo))
