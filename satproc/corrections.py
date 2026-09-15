from __future__ import annotations

import numpy as np


def apply_radiometric_scaling_if_available(data: np.ndarray, metadata: dict) -> np.ndarray:
    """
    Applies scale/offset only when explicitly available.

    Scientific assumption: no generic atmospheric/radiometric correction is applied
    without product-specific coefficients to avoid introducing non-physical values.
    """
    coeffs = metadata.get("radiometric_coefficients")
    if not coeffs:
        return data

    gain = float(coeffs.get("gain", 1.0))
    offset = float(coeffs.get("offset", 0.0))
    return data * gain + offset
