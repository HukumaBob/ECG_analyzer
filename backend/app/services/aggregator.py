"""
Агрегация вероятностей по сегментам.

Принимает матрицу [N, 17] (N сегментов × 17 классов),
возвращает финальный вектор [17] для всей записи.

Стратегия:
  - По умолчанию: max по сегментам (консервативно, не пропускаем эпизоды)
  - Дополнительно возвращаем mean для информации
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def aggregate(probs: np.ndarray) -> dict[str, np.ndarray]:
    """
    Parameters
    ----------
    probs : np.ndarray
        shape [N, 17], float32

    Returns
    -------
    dict с ключами:
        "max"  : [17] float32 — максимум по сегментам (используется как основной)
        "mean" : [17] float32 — среднее по сегментам (для информации)
        "per_segment" : [N, 17] — исходная матрица (для saliency в будущем)
    """
    if probs.ndim != 2 or probs.shape[1] != 17:
        raise ValueError(f"Ожидается shape [N, 17], получено: {probs.shape}")

    agg_max = probs.max(axis=0).astype(np.float32)
    agg_mean = probs.mean(axis=0).astype(np.float32)

    logger.debug(
        "Aggregation: %d segments → max top-3: %s",
        len(probs),
        np.argsort(agg_max)[::-1][:3].tolist(),
    )

    return {
        "max": agg_max,
        "mean": agg_mean,
        "per_segment": probs,
    }
