from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA


def band_index_from_wavelength(wavelengths_nm: list[float], target_nm: float) -> int:
    if not wavelengths_nm:
        raise ValueError("No wavelength metadata available for wavelength-based lookup.")
    arr = np.asarray(wavelengths_nm, dtype=np.float32)
    finite_idx = np.where(np.isfinite(arr))[0]
    if finite_idx.size == 0:
        raise ValueError("Wavelength metadata exists but has no valid numeric values.")
    nearest_local = int(np.argmin(np.abs(arr[finite_idx] - float(target_nm))))
    return int(finite_idx[nearest_local])


def extract_pixel_spectrum(data: np.ndarray, row: int, col: int) -> np.ndarray:
    if row < 0 or col < 0 or row >= data.shape[1] or col >= data.shape[2]:
        raise ValueError("Selected pixel is outside image bounds.")
    return data[:, row, col]


def pca_cube(data: np.ndarray, n_components: int = 3) -> np.ndarray:
    bands, rows, cols = data.shape
    flat = data.reshape(bands, rows * cols).T
    model = PCA(n_components=n_components)
    pca_data = model.fit_transform(flat)
    return pca_data.T.reshape(n_components, rows, cols)


def band_stats(data: np.ndarray, band_index: int) -> dict[str, float]:
    band = data[band_index]
    return {
        "min": float(np.nanmin(band)),
        "max": float(np.nanmax(band)),
        "mean": float(np.nanmean(band)),
        "std": float(np.nanstd(band)),
    }
