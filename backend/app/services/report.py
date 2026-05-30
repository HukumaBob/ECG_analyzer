"""
Формирование диагностических меток и текстового заключения.

Шаблоны — на русском и английском языках, без LLM.
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
    # label, label_ru, label_en, priority, threshold
    {"label": "poor_data_quality",      "label_ru": "Низкое качество сигнала",               "label_en": "Poor signal quality",               "priority": Priority.TECHNICAL, "threshold": 0.5},
    {"label": "sinus_rhythm",           "label_ru": "Синусовый ритм",                        "label_en": "Sinus rhythm",                      "priority": Priority.NORMAL,    "threshold": 0.5},
    {"label": "pvc",                    "label_ru": "ЖЭС (желудочковая экстрасистолия)",     "label_en": "PVC (premature ventricular complex)","priority": Priority.MODERATE,  "threshold": 0.5},
    {"label": "tachycardia",            "label_ru": "Тахикардия",                            "label_en": "Tachycardia",                       "priority": Priority.MODERATE,  "threshold": 0.5},
    {"label": "ventricular_tachycardia","label_ru": "Желудочковая тахикардия (ЖТ)",          "label_en": "Ventricular tachycardia (VT)",       "priority": Priority.CRITICAL,  "threshold": 0.4},
    {"label": "svt_with_aberrancy",     "label_ru": "СВТ с аберрантным проведением",         "label_en": "SVT with aberrancy",                "priority": Priority.HIGH,      "threshold": 0.5},
    {"label": "atrial_fibrillation",    "label_ru": "Фибрилляция предсердий (ФП)",           "label_en": "Atrial fibrillation (AF)",           "priority": Priority.HIGH,      "threshold": 0.5},
    {"label": "atrial_flutter",         "label_ru": "Трепетание предсердий",                 "label_en": "Atrial flutter",                    "priority": Priority.HIGH,      "threshold": 0.5},
    {"label": "bradycardia",            "label_ru": "Брадикардия",                           "label_en": "Bradycardia",                       "priority": Priority.MODERATE,  "threshold": 0.5},
    {"label": "accessory_pathway_wpw",  "label_ru": "Проведение по ДПП (синдром WPW)",       "label_en": "Accessory pathway (WPW syndrome)",  "priority": Priority.HIGH,      "threshold": 0.5},
    {"label": "av_block_2_3",           "label_ru": "АВ-блокада II–III ст.",                 "label_en": "AV block II–III degree",            "priority": Priority.HIGH,      "threshold": 0.5},
    {"label": "av_block_1",             "label_ru": "АВ-блокада I степени",                  "label_en": "1st degree AV block",               "priority": Priority.MODERATE,  "threshold": 0.5},
    {"label": "bifascicular_block",     "label_ru": "Бифасцикулярная блокада",               "label_en": "Bifascicular block",                "priority": Priority.MODERATE,  "threshold": 0.5},
    {"label": "rbbb",                   "label_ru": "Блокада правой ножки пучка Гиса",       "label_en": "Right bundle branch block (RBBB)",  "priority": Priority.MODERATE,  "threshold": 0.5},
    {"label": "lbbb",                   "label_ru": "Блокада левой ножки пучка Гиса",        "label_en": "Left bundle branch block (LBBB)",   "priority": Priority.MODERATE,  "threshold": 0.5},
    {"label": "infarction",             "label_ru": "Инфаркт / инфарктоподобные изменения",  "label_en": "Infarction / infarction-like changes","priority": Priority.CRITICAL, "threshold": 0.4},
    {"label": "electronic_pacemaker",   "label_ru": "Электронный кардиостимулятор",          "label_en": "Electronic pacemaker",              "priority": Priority.TECHNICAL, "threshold": 0.5},
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
    List[DiagnosisItem] — 17 элементов, triggered сначала, затем по убыванию вероятности
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
            label_en=meta["label_en"],
            probability=round(p, 4),
            triggered=triggered,
            priority=meta["priority"],
        ))

    items.sort(key=lambda x: (not x.triggered, -x.probability))
    return items


def build_conclusion(diagnoses: list[DiagnosisItem], poor_quality: bool) -> tuple[str, str]:
    """
    Возвращает (conclusion_ru, conclusion_en) по шаблонам.
    """
    return (
        _conclusion_ru(diagnoses, poor_quality),
        _conclusion_en(diagnoses, poor_quality),
    )


def check_poor_quality(diagnoses: list[DiagnosisItem]) -> bool:
    for d in diagnoses:
        if d.label == "poor_data_quality" and d.triggered:
            return True
    return False


# ---------------------------------------------------------------------------
# Шаблоны на русском
# ---------------------------------------------------------------------------


def _conclusion_ru(diagnoses: list[DiagnosisItem], poor_quality: bool) -> str:
    triggered = {d.label: d for d in diagnoses if d.triggered}
    lines: list[str] = []

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
    lines.append(f"Ритм: {', '.join(rhythm_parts)}." if rhythm_parts else "Ритм: не определён достоверно.")

    if "tachycardia" in triggered and "bradycardia" in triggered:
        lines.append("ЧСС: чередование тахи- и брадикардии.")
    elif "tachycardia" in triggered:
        lines.append("ЧСС: тахикардия.")
    elif "bradycardia" in triggered:
        lines.append("ЧСС: брадикардия.")

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
    lines.append(f"Проводимость: {', '.join(conduction_parts)}." if conduction_parts else "Проводимость: нарушений не выявлено.")

    lines.append("Реполяризация: инфарктоподобные изменения." if "infarction" in triggered else "Реполяризация: без значимых изменений.")

    critical_found = [d.label_ru for d in diagnoses if d.triggered and d.label in CRITICAL_LABELS]
    if critical_found:
        summary = "КРИТИЧЕСКАЯ НАХОДКА: " + "; ".join(critical_found) + "."
    elif not triggered or set(triggered) <= {"sinus_rhythm"}:
        summary = "Патологических изменений не выявлено."
    else:
        non_tech = [d.label_ru for d in diagnoses if d.triggered and d.priority not in (Priority.TECHNICAL, Priority.NORMAL)]
        summary = "Выявлены изменения: " + "; ".join(non_tech) + "." if non_tech else "Изменения умеренной значимости."
    lines.append(f"Заключение: {summary}")

    if poor_quality:
        lines.append("⚠ Предупреждение: низкое качество сигнала. Достоверность заключения снижена.")

    lines.append(
        "Примечание: анализ выполнен автоматически на основе модели ECG-FM. "
        "Требует верификации врачом. Не является медицинским диагнозом."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Шаблоны на английском
# ---------------------------------------------------------------------------


def _conclusion_en(diagnoses: list[DiagnosisItem], poor_quality: bool) -> str:
    triggered = {d.label: d for d in diagnoses if d.triggered}
    lines: list[str] = []

    rhythm_parts: list[str] = []
    if "sinus_rhythm" in triggered:
        rhythm_parts.append("sinus")
    if "atrial_fibrillation" in triggered:
        rhythm_parts.append("atrial fibrillation")
    if "atrial_flutter" in triggered:
        rhythm_parts.append("atrial flutter")
    if "ventricular_tachycardia" in triggered:
        rhythm_parts.append("ventricular tachycardia")
    if "svt_with_aberrancy" in triggered:
        rhythm_parts.append("SVT with aberrancy")
    if "pvc" in triggered:
        rhythm_parts.append("premature ventricular complexes")
    if "electronic_pacemaker" in triggered:
        rhythm_parts.append("pacemaker rhythm")
    lines.append(f"Rhythm: {', '.join(rhythm_parts)}." if rhythm_parts else "Rhythm: not reliably determined.")

    if "tachycardia" in triggered and "bradycardia" in triggered:
        lines.append("Heart rate: alternating tachycardia and bradycardia.")
    elif "tachycardia" in triggered:
        lines.append("Heart rate: tachycardia.")
    elif "bradycardia" in triggered:
        lines.append("Heart rate: bradycardia.")

    conduction_parts: list[str] = []
    if "av_block_2_3" in triggered:
        conduction_parts.append("AV block II–III degree")
    if "av_block_1" in triggered:
        conduction_parts.append("1st degree AV block")
    if "rbbb" in triggered:
        conduction_parts.append("RBBB")
    if "lbbb" in triggered:
        conduction_parts.append("LBBB")
    if "bifascicular_block" in triggered:
        conduction_parts.append("bifascicular block")
    if "accessory_pathway_wpw" in triggered:
        conduction_parts.append("accessory pathway conduction")
    lines.append(f"Conduction: {', '.join(conduction_parts)}." if conduction_parts else "Conduction: no abnormalities detected.")

    lines.append("Repolarization: infarction-like changes." if "infarction" in triggered else "Repolarization: no significant changes.")

    critical_found = [d.label_en for d in diagnoses if d.triggered and d.label in CRITICAL_LABELS]
    if critical_found:
        summary = "CRITICAL FINDING: " + "; ".join(critical_found) + "."
    elif not triggered or set(triggered) <= {"sinus_rhythm"}:
        summary = "No pathological changes detected."
    else:
        non_tech = [d.label_en for d in diagnoses if d.triggered and d.priority not in (Priority.TECHNICAL, Priority.NORMAL)]
        summary = "Findings: " + "; ".join(non_tech) + "." if non_tech else "Findings of moderate significance."
    lines.append(f"Conclusion: {summary}")

    if poor_quality:
        lines.append("⚠ Warning: poor signal quality. Reliability of the report is reduced.")

    lines.append(
        "Note: analysis performed automatically using the ECG-FM model. "
        "Requires physician verification. Not a medical diagnosis."
    )
    return "\n".join(lines)
