# ECG Interpreter

A web-based system for automated 12-lead ECG analysis, generating auxiliary diagnostic conclusions for clinicians.

> **Disclaimer:** This system is not a certified medical diagnostic device. All outputs are advisory only and must be reviewed by a qualified physician.

[Документация на русском](README.ru.md)

## Overview

- **Backend:** FastAPI + PyTorch, powered by [ECG-FM](https://github.com/bowang-lab/ECG-FM) (wav2vec 2.0 architecture), 17 diagnostic classes
- **Frontend:** React + Recharts/Plotly.js
- **Supported ECG formats:** WFDB (.hea/.dat), MATLAB (.mat), CSV

## Prerequisites

- Python 3.11
- [uv](https://docs.astral.sh/uv/) — Python package manager
- Node.js ≥ 18
- [fairseq-signals](https://github.com/Jwoo5/fairseq-signals) — must be installed manually as an editable install
- ECG-FM model checkpoint (see below)

## Installation

### 1. fairseq-signals (required before backend setup)

fairseq-signals requires an editable install and is not included in `pyproject.toml`:

```bash
git clone https://github.com/Jwoo5/fairseq-signals.git /path/to/fairseq-signals
cd backend
uv pip install -e /path/to/fairseq-signals/
```

### 2. Backend

```bash
cd backend
uv sync
```

Optionally, set a custom uv cache directory:

```bash
export UV_CACHE_DIR=/path/to/uv-cache
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Model checkpoint

The ECG-FM checkpoint is not included in this repository. Download it from [HuggingFace](https://huggingface.co/wanglab/ecg-fm) and place the files at a path of your choice:

```
/path/to/ECG-FM/ckpts/mimic_iv_ecg_finetuned.pt
/path/to/ECG-FM/ckpts/mimic_iv_ecg_finetuned.yaml
```

## Running

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

Open in browser: http://localhost:5173

## Environment Variables

| Variable | Required | Description |
|----------|:--------:|-------------|
| `HF_HOME` | yes | Path to Hugging Face cache |
| `ECG_FM_CKPT` | yes | Path to the `.pt` model checkpoint |
| `UV_CACHE_DIR` | no | Custom uv cache directory |

## Reproducibility

- `backend/uv.lock` — pinned Python dependency versions, committed to the repository
- `frontend/package-lock.json` — pinned npm dependency versions, committed to the repository
- fairseq-signals — editable install, path is local to each developer, not included in lock files

## Diagnostic Classes

The model outputs probabilities for 17 classes. **Ventricular tachycardia** and **Infarction** are flagged as critical and displayed with a visual alert.

| # | Class | Priority |
|---|-------|----------|
| 1 | Poor data quality | Technical |
| 2 | Sinus rhythm | Normal |
| 3 | PVC | Moderate |
| 4 | Tachycardia | Moderate |
| 5 | **Ventricular tachycardia** | **CRITICAL** |
| 6 | SVT with aberrancy | High |
| 7 | Atrial fibrillation | High |
| 8 | Atrial flutter | High |
| 9 | Bradycardia | Moderate |
| 10 | Accessory pathway (WPW) | High |
| 11 | AV block II–III | High |
| 12 | 1st degree AV block | Moderate |
| 13 | Bifascicular block | Moderate |
| 14 | RBBB | Moderate |
| 15 | LBBB | Moderate |
| 16 | **Infarction** | **CRITICAL** |
| 17 | Electronic pacemaker | Technical |

## Performance Requirements

- CPU inference: ≤ 30 s
- GPU inference: ≤ 5 s
- Minimum recording length: 10 seconds
- Input signal is resampled to 500 Hz

## Acknowledgements

This project is built on top of **ECG-FM**, an open electrocardiogram foundation model developed by [Wang Lab, University of Toronto](https://github.com/bowang-lab).

- GitHub: https://github.com/bowang-lab/ECG-FM
- Model weights (HuggingFace): https://huggingface.co/wanglab/ecg-fm
- Paper: https://arxiv.org/abs/2408.05178
- License: MIT

The ECG-FM model is built on the [fairseq-signals](https://github.com/Jwoo5/fairseq-signals) framework by JW Oh et al.

If you use this system in research, please cite the original work:

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

## License

This project is licensed under the MIT License.
