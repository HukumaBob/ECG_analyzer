# ЭКГ-Интерпретатор

[English documentation](README.md)

Веб-система автоматического анализа 12-канальных ЭКГ с формированием вспомогательного диагностического заключения для врача поликлиники.

> **Внимание:** система не является медицинским диагностическим прибором. Все выводы носят вспомогательный характер.

## Архитектура

- **Backend:** FastAPI + PyTorch, модель ECG-FM (wav2vec 2.0), 17 диагностических классов
- **Frontend:** React + Recharts/Plotly.js
- **Форматы ЭКГ:** WFDB (.hea/.dat), MATLAB (.mat), CSV

## Предусловия

- Python 3.11
- [uv](https://docs.astral.sh/uv/) — менеджер пакетов Python
- Node.js ≥ 18
- Репозиторий [fairseq-signals](https://github.com/facebookresearch/fairseq-signals) — устанавливается вручную как editable install
- Чекпойнт модели ECG-FM (см. ниже)

## Установка

### 1. fairseq-signals (обязательно, до backend)

fairseq-signals требует editable install и не включён в `pyproject.toml`:

```bash
git clone https://github.com/facebookresearch/fairseq-signals.git /path/to/fairseq-signals
cd backend
uv pip install -e /path/to/fairseq-signals/
```

### 2. Backend

```bash
cd backend
uv sync
```

Опционально — задать кеш uv (если нужно вынести с системного диска):

```bash
export UV_CACHE_DIR=/path/to/uv-cache
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Чекпойнт модели

Модель ECG-FM не входит в репозиторий. Скопируйте файлы чекпойнта в директорию вне репозитория и укажите путь при запуске:

```
/path/to/ECG-FM/ckpts/mimic_iv_ecg_finetuned.pt
/path/to/ECG-FM/ckpts/mimic_iv_ecg_finetuned.yaml
```

## Запуск

### Backend

```bash
cd backend
HF_HOME=/path/to/hf-cache \
ECG_FM_CKPT=/path/to/ECG-FM/ckpts/mimic_iv_ecg_finetuned.pt \
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm run dev
```

Открыть в браузере: http://localhost:5173

## Переменные окружения

| Переменная | Обязательная | Описание |
|------------|:---:|---------|
| `HF_HOME` | да | Путь к кешу Hugging Face |
| `ECG_FM_CKPT` | да | Путь к `.pt` чекпойнту модели |
| `UV_CACHE_DIR` | нет | Путь к кешу uv (по умолчанию — системный) |

## Воспроизводимость окружения

- `backend/uv.lock` — зафиксированные версии Python-зависимостей, коммитится в репозиторий
- `frontend/package-lock.json` — зафиксированные версии npm-зависимостей, коммитится в репозиторий
- fairseq-signals — editable install, путь у каждого разработчика свой, в lock-файл не входит

## Диагностические классы

Модель выдаёт вероятности по 17 классам. Классы **Ventricular tachycardia** и **Infarction** помечаются как критические и отображаются с визуальным акцентом.

Полное описание классов и приоритетов — в [ТЗ_Интерпретатор_ЭКГ_v1.md](ТЗ_Интерпретатор_ЭКГ_v1.md).

## Требования к производительности

- Inference на CPU: ≤ 30 сек
- Inference на GPU: ≤ 5 сек
- Минимальная длина записи: 10 секунд
- Входной сигнал ресемплируется до 500 Hz

## Используемая модель

Система использует **ECG-FM** — foundation model для анализа ЭКГ, разработанную [Wang Lab (University of Toronto)](https://github.com/bowang-lab).

- GitHub: https://github.com/bowang-lab/ECG-FM
- Веса модели (HuggingFace): https://huggingface.co/wanglab/ecg-fm
- Препринт: https://arxiv.org/abs/2408.05178
- Лицензия модели: MIT
- Зависимость: [fairseq-signals](https://github.com/Jwoo5/fairseq-signals) (JW Oh et al.)

Если вы используете эту систему в исследовательских целях, пожалуйста, сошлитесь на оригинальную работу:

```bibtex
@article{mckeen2024ecgfm,
  title   = {ECG-FM: An Open Electrocardiogram Foundation Model},
  author  = {McKeen, Kaden and Masood, Sameer and Toma, Augustin and Rubin, Barry and Wang, Bo},
  journal = {arXiv preprint arXiv:2408.05178},
  year    = {2024},
  doi     = {10.48550/arXiv.2408.05178},
  url     = {https://arxiv.org/abs/2408.05178}
}
```
