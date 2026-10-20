from __future__ import annotations
import numpy as np

def normalized_difference_arrays(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a.astype(np.float32, copy=False)
    b = b.astype(np.float32, copy=False)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (a - b) / (a + b)
    out[~np.isfinite(out)] = np.nan
    return out
