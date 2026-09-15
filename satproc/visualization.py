from __future__ import annotations

import numpy as np


def stretch_to_uint8(arr: np.ndarray, low_pct: float = 2.0, high_pct: float = 98.0) -> np.ndarray:
    lo = np.nanpercentile(arr, low_pct)
    hi = np.nanpercentile(arr, high_pct)
    if hi <= lo:
        return np.zeros_like(arr, dtype=np.uint8)
    scaled = np.clip((arr - lo) / (hi - lo), 0, 1)
    return (scaled * 255).astype(np.uint8)


def rgb_composite(data: np.ndarray, r_idx: int, g_idx: int, b_idx: int) -> np.ndarray:
    r = stretch_to_uint8(data[r_idx])
    g = stretch_to_uint8(data[g_idx])
    b = stretch_to_uint8(data[b_idx])
    return np.dstack([r, g, b])
