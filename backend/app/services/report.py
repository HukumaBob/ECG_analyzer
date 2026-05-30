"""
Формирование диагностических меток и текстового заключения.

Все тексты — шаблоны на русском языке, без LLM.
Пороги активации подобраны консервативно (0.5 по умолчанию).
Критические классы (ЖТ, Инфаркт) имеют пониженный порог для высокой чувствительности.
"""

from __future__ import annotations

import numpy as np

from app.schemas import DiagnosisItem, Priority

# ---------------------------------------------------------------------------
# Метаданные классов
# ---------------------------------------------------------------------------

CLASS_META: list[dict] = [
    # idx, label, label_ru, priority, threshold
    {"label": "poor_data_quality",     "label_ru": "Низкое качество сигнала",              "priority": Priority.TECHNICAL,  "threshold": 0.5},
    {"label": "sinus_rhythm",          "label_ru": "Синусовый ритм",                       "priority": Priority.NORMAL,     "threshold": 0.5},
    {"label": "pvc",                   "label_ru": "ЖЭС (желудочковая экстрасистолия)",    "priority": Priority.MODERATE,   "threshold": 0.5},
    {"label": "tachycardia",           "label_ru": "Тахикардия",                           "priority": Priority.MODERATE,   "threshold": 0.5},
    {"label": "ventricular_tachycardia","label_ru": "Желудочковая тахикардия (ЖТ)",        "priority": Priority.CRITICAL,   "threshold": 0.4},
    {"label": "svt_with_aberrancy",    "label_ru": "СВТ с аберрантным проведением",       "priority": Priority.HIGH,       "threshold": 0.5},
    {"label": "atrial_fibrillation",   "label_ru": "Фибрилляция предсердий (ФП)",         "priority": Priority.HIGH,       "threshold": 0.5},
    {"label": "atrial_flutter",        "label_ru": "Трепетание предсердий",               "priority": Priority.HIGH,       "threshold": 0.5},
    {"label": "bradycardia",           "label_ru": "Брадикардия",                         "priority": Priority.MODERATE,   "threshold": 0.5},
    {"label": "accessory_pathway_wpw", "label_ru": "Проведение по ДПП (синдром WPW)",     "priority": Priority.HIGH,       "threshold": 0.5},
    {"label": "av_block_2_3",          "label_ru": "АВ-блокада II–III ст.",               "priority": Priority.HIGH,       "threshold": 0.5},
    {"label": "av_block_1",            "label_ru": "АВ-блокада I степени",                "priority": Priority.MODERATE,   "threshold": 0.5},
    {"label": "bifascicular_block",    "label_ru": "Бифасцикулярная блокада",             "priority": Priority.MODERATE,   "threshold": 0.5},
    {"label": "rbbb",                  "label_ru": "Блокада правой ножки пучка Гиса",     "priority": Priority.MODERATE,   "threshold": 0.5},
    {"label": "lbbb",                  "label_ru": "Блокада левой ножки пучка Гиса",      "priority": Priority.MODERATE,   "threshold": 0.5},
    {"label": "infarction",            "label_ru": "Инфаркт / инфарктоподобные изменения","priority": Priority.CRITICAL,   "threshold": 0.4},
    {"label": "electronic_pacemaker",  "label_ru": "Электронный кардиостимулятор",        "priority": Priority.TECHNICAL,  "threshold": 0.5},
]

assert len(CLASS_META) == 17, "Должно быть ровно 17 классов"

CRITICAL_LABELS = {"ventricular_tachycardia", "infarction"}


# ---------------------------------------------------------------------------
# Публичный интерфейс
# ---------------------------------------------------------------------------


def build_diagnoses(probs: np.ndarray) -> list[DiagnosisItem]:
    """
    Parameters
    ----------
    probs : np.ndarray
        shape [17], float32

    Returns
    -------
    List[DiagnosisItem]  — 17 элементов, отсортированных: triggered сначала, затем по убыванию вероятности
    """
    if len(probs) != 17:
        raise ValueError(f"Ожидается вектор длиной 17, получено {len(probs)}")

    items = []
    for i, meta in enumerate(CLASS_META):
        p = float(probs[i])
        triggered = p >= meta["threshold"]
        items.append(DiagnosisItem(
            label=meta["label"],
            label_ru=meta["label_ru"],
            probability=round(p, 4),
            triggered=triggered,
            priority=meta["priority"],
        ))

    # Triggered — сначала, внутри группы — по убыванию вероятности
    items.sort(key=lambda x: (not x.triggered, -x.probability))
    return items


def build_conclusion(diagnoses: list[DiagnosisItem], poor_quality: bool) -> str:
    """
    Генерирует текстовое заключение на русском языке по шаблонам.
    """
    triggered = {d.label: d for d in diagnoses if d.triggered}

    lines: list[str] = []

    # --- Ритм ---
    rhythm_parts: list[str] = []
    if "sinus_rhythm" in triggered:
        rhythm_parts.append("синусовый")
    if "atrial_fibrillation" in triggered:
        rhythm_parts.append("фибрилляция предсердий")
    if "atrial_flutter" in triggered:
        rhythm_parts.append("трепетание предсердий")
    if "ventricular_tachycardia" in triggered:
        rhythm_parts.append("желудочковая тахикардия")
    if "svt_with_aberrancy" in triggered:
        rhythm_parts.append("СВТ с аберрантным проведением")
    if "pvc" in triggered:
        rhythm_parts.append("желудочковые экстрасистолы")
    if "electronic_pacemaker" in triggered:
        rhythm_parts.append("ритм кардиостимулятора")

    if rhythm_parts:
        lines.append(f"Ритм: {', '.join(rhythm_parts)}.")
    else:
        lines.append("Ритм: не определён достоверно.")

    # --- ЧСС ---
    if "tachycardia" in triggered and "bradycardia" in triggered:
        lines.append("ЧСС: чередование тахи- и брадикардии.")
    elif "tachycardia" in triggered:
        lines.append("ЧСС: тахикардия.")
    elif "bradycardia" in triggered:
        lines.append("ЧСС: брадикардия.")

    # --- Проводимость ---
    conduction_parts: list[str] = []
    if "av_block_2_3" in triggered:
        conduction_parts.append("АВ-блокада II–III ст.")
    if "av_block_1" in triggered:
        conduction_parts.append("АВ-блокада I ст.")
    if "rbbb" in triggered:
        conduction_parts.append("блокада ПНПГ")
    if "lbbb" in triggered:
        conduction_parts.append("блокада ЛНПГ")
    if "bifascicular_block" in triggered:
        conduction_parts.append("бифасцикулярная блокада")
    if "accessory_pathway_wpw" in triggered:
        conduction_parts.append("проведение по ДПП")

    if conduction_parts:
        lines.append(f"Проводимость: {', '.join(conduction_parts)}.")
    else:
        lines.append("Проводимость: нарушений не выявлено.")

    # --- Реполяризация ---
    if "infarction" in triggered:
        lines.append("Реполяризация: инфарктоподобные изменения.")
    else:
        lines.append("Реполяризация: без значимых изменений.")

    # --- Итоговая фраза ---
    critical_found = [d.label_ru for d in diagnoses if d.triggered and d.label in CRITICAL_LABELS]
    if critical_found:
        summary = "КРИТИЧЕСКАЯ НАХОДКА: " + "; ".join(critical_found) + "."
    elif not triggered or set(triggered) <= {"sinus_rhythm"}:
        summary = "Патологических изменений не выявлено."
    else:
        non_tech = [d.label_ru for d in diagnoses if d.triggered and d.priority not in (Priority.TECHNICAL, Priority.NORMAL)]
        summary = "Выявлены изменения: " + "; ".join(non_tech) + "." if non_tech else "Изменения умеренной значимости."

    lines.append(f"Заключение: {summary}")

    # --- Предупреждение о качестве ---
    if poor_quality:
        lines.append(
            "⚠ Предупреждение: низкое качество сигнала. Достоверность заключения снижена."
        )

    lines.append(
        "Примечание: анализ выполнен автоматически на основе модели ECG-FM. "
        "Требует верификации врачом. Не является медицинским диагнозом."
    )

    return "\n".join(lines)


def check_poor_quality(diagnoses: list[DiagnosisItem]) -> bool:
    for d in diagnoses:
        if d.label == "poor_data_quality" and d.triggered:
            return True
    return False
