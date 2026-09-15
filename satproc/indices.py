from __future__ import annotations

import numpy as np


def normalized_difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    denom = a + b
    out = np.zeros_like(a, dtype=np.float32)
    valid = np.abs(denom) > 1e-10
    out[valid] = (a[valid] - b[valid]) / denom[valid]
    return out
