"""
Inference-обёртка над ECG-FM.

Принимает сегменты [N, 12, 2500] float32,
возвращает матрицу вероятностей [N, 17] float32.

forward(): source=[B, 12, T] → {"out": [B, 17] logits}
Задача multi-label → sigmoid, не softmax.
"""

import logging

import numpy as np
import torch

from app.services.loader import ModelLoader

logger = logging.getLogger(__name__)

BATCH_SIZE = 4   # сегменты на GPU за раз; снижается при нехватке памяти


def run_inference(segments: np.ndarray) -> np.ndarray:
    """
    Parameters
    ----------
    segments : np.ndarray
        shape [N, 12, 2500], float32

    Returns
    -------
    probs : np.ndarray
        shape [N, 17], float32 — вероятности по 17 классам для каждого сегмента
    """
    loader = ModelLoader.get_instance()
    model = loader.model
    device = loader.device

    n_segments = len(segments)
    all_probs: list[np.ndarray] = []

    model.eval()
    with torch.no_grad():
        for start in range(0, n_segments, BATCH_SIZE):
            batch_np = segments[start : start + BATCH_SIZE]  # [B, 12, 2500]
            source = torch.from_numpy(batch_np).to(device)   # [B, 12, 2500]

            # padding_mask=None означает «все токены валидны»
            net_output = model(source=source, padding_mask=None)

            logits = net_output["out"]   # [B, 17]
            probs = torch.sigmoid(logits).cpu().numpy().astype(np.float32)
            all_probs.append(probs)

            logger.debug(
                "Inference batch %d-%d: logits min=%.3f max=%.3f",
                start,
                start + len(batch_np) - 1,
                float(logits.min()),
                float(logits.max()),
            )

    result = np.concatenate(all_probs, axis=0)  # [N, 17]
    logger.info("Inference done: %d segments → probs shape %s", n_segments, result.shape)
    return result
