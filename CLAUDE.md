# ЭКГ-Интерпретатор — CLAUDE.md

## Описание проекта

**ЭКГ-Интерпретатор** — веб-система автоматического анализа 12-канальных ЭКГ с формированием вспомогательного диагностического заключения для врача поликлиники.

Система **не является медицинским диагностическим прибором**. Все выводы носят вспомогательный характер.

**ТЗ:** [ТЗ_Интерпретатор_ЭКГ_v1.md](ТЗ_Интерпретатор_ЭКГ_v1.md)

---

## Архитектура

```
ECG/ (этот проект)
├── CLAUDE.md
├── ТЗ_Интерпретатор_ЭКГ_v1.md
├── backend/           # FastAPI, ML-обработка
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── services/
│   │   │   ├── preprocessor.py   # конвертация, ресемплинг → 500Hz, нарезка
│   │   │   ├── inference.py      # обёртка над ECG-FM
│   │   │   ├── aggregator.py     # агрегация по сегментам
│   │   │   ├── bayes.py          # байесовская поправка
│   │   │   └── report.py         # генерация текстового заключения
│   │   └── models/               # Pydantic-схемы
│   └── pyproject.toml
└── frontend/          # React SPA
    └── src/
```

**Смежные репозитории** (уже есть на диске):
- `/mnt/work-disk/Documents/Dev/ECG-FM/` — исходный репозиторий ECG-FM с весами и ноутбуками
- `/mnt/work-disk/Documents/Dev/fairseq-signals/` — зависимость (editable install)

---

## Модель

- **Чекпойнт:** `/mnt/work-disk/Documents/Dev/ECG-FM/ckpts/mimic_iv_ecg_finetuned.pt`
- **Конфиг:** `/mnt/work-disk/Documents/Dev/ECG-FM/ckpts/mimic_iv_ecg_finetuned.yaml`
- 17 диагностических классов (multi-label)
- Архитектура: wav2vec 2.0 через fairseq-signals

---

## Технологический стек

| Слой | Технология |
|------|-----------|
| ML-бэкенд | Python 3.11, fairseq-signals (editable), PyTorch |
| API-сервер | FastAPI + uvicorn |
| Фронтенд | React + Recharts (или Plotly.js) для графиков ЭКГ |
| Форматы ЭКГ | WFDB (.hea/.dat), MATLAB (.mat), CSV |
| Деплой | Локальный сервер поликлиники, без облака |

---

## Диагностические классы (17 штук)

| # | Класс | Приоритет |
|---|-------|-----------|
| 1 | Poor data quality | Технический |
| 2 | Sinus rhythm | Норма |
| 3 | PVC (ЖЭС) | Умеренная |
| 4 | Tachycardia | Умеренная |
| 5 | **Ventricular tachycardia** | **КРИТИЧЕСКАЯ** |
| 6 | SVT with aberrancy | Высокая |
| 7 | Atrial fibrillation | Высокая |
| 8 | Atrial flutter | Высокая |
| 9 | Bradycardia | Умеренная |
| 10 | Accessory pathway (WPW) | Высокая |
| 11 | AV block II–III | Высокая |
| 12 | 1st degree AV block | Умеренная |
| 13 | Bifascicular block | Умеренная |
| 14 | RBBB | Умеренная |
| 15 | LBBB | Умеренная |
| 16 | **Infarction** | **КРИТИЧЕСКАЯ** |
| 17 | Electronic pacemaker | Технический |

Классы 5 и 16 — флаги тревоги, выводятся с визуальным акцентом.

---

## Окружение

- Python: 3.11
- Менеджер пакетов: **uv**
- Переменные окружения:
  - `HF_HOME=/mnt/work-disk/.hf-cache`
  - `UV_CACHE_DIR=/mnt/work-disk/.uv-cache`
- fairseq-signals — только editable install, иначе модель не загружается

---

## Правила работы

- Не устанавливать пакеты без подтверждения пользователя
- Не трогать директорию `/mnt/work-disk/Documents/Dev/ECG-FM/` — это upstream, не наш код
- Байесовская поправка — простая таблица prior-смещений, без ML
- Текстовые заключения — шаблоны на русском, без LLM
- ЭКГ и данные пациентов не должны покидать локальную сеть
- При добавлении обработчиков форматов — всегда добавлять graceful error handling

---

## Нефункциональные ограничения

- Inference на CPU: ≤ 30 сек; на GPU: ≤ 5 сек
- Браузер: Chrome, Firefox без установки клиентского ПО
- Минимальная запись ЭКГ: 10 секунд (2 сегмента по 5 сек)
- Ресемплинг входного сигнала → 500 Hz (формат ECG-FM)
