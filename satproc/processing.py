from __future__ import annotations

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window
from sklearn.decomposition import PCA

from .indices import normalized_difference_arrays

def _preview_dimensions(width, height, max_dim=900):
    scale = min(max_dim / width, max_dim / height, 1.0)
    return max(1, int(height * scale)), max(1, int(width * scale))

def _replace_nodata(data, nodata):
    data = data.astype(np.float32, copy=False)
    if nodata is not None:
        data[data == nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data

def percentile_stretch(array, low=2, high=98, sample_size=200_000):
    arr = np.asarray(array, dtype=np.float32)
    finite = np.isfinite(arr)
    if not finite.any():
        return np.zeros_like(arr, dtype=np.float32)
    valid = arr[finite]
    if valid.size > sample_size:
        step = max(1, valid.size // sample_size)
        sample = valid[::step][:sample_size]
    else:
        sample = valid
    minimum, maximum = np.percentile(sample, [low, high])
    if maximum <= minimum:
        return np.zeros_like(arr, dtype=np.float32)
    out = np.empty_like(arr, dtype=np.float32)
    np.subtract(arr, minimum, out=out)
    out /= np.float32(maximum - minimum)
    np.clip(out, 0, 1, out=out)
    out[~finite] = 0
    return out

def read_band_preview(path, band=1, max_dim=900):
    with rasterio.open(path) as src:
        h, w = _preview_dimensions(src.width, src.height, max_dim)
        data = src.read(band, out_shape=(h, w), resampling=Resampling.bilinear)
        return _replace_nodata(data, src.nodata)

def read_rgb_preview(path, red_band, green_band, blue_band, low=2, high=98, max_dim=900):
    indexes = [red_band, green_band, blue_band]
    with rasterio.open(path) as src:
        h, w = _preview_dimensions(src.width, src.height, max_dim)
        cube = src.read(indexes, out_shape=(3, h, w), resampling=Resampling.bilinear)
        cube = _replace_nodata(cube, src.nodata)
    stretched = [percentile_stretch(cube[i], low, high) for i in range(3)]
    return np.moveaxis(np.stack(stretched, axis=0), 0, -1)

def read_rgb_files(red_path, green_path, blue_path, low=2, high=98, max_dim=900):
    paths = [red_path, green_path, blue_path]
    with rasterio.open(paths[0]) as ref:
        h, w = _preview_dimensions(ref.width, ref.height, max_dim)
    result = []
    for path in paths:
        with rasterio.open(path) as src:
            arr = src.read(1, out_shape=(h, w), resampling=Resampling.bilinear)
            arr = _replace_nodata(arr, src.nodata)
            result.append(percentile_stretch(arr, low, high))
    return np.dstack(result).astype(np.float32, copy=False)

def calculate_stats(path, band=1, max_dim=600):
    arr = read_band_preview(path, band=band, max_dim=max_dim)
    valid = arr[np.isfinite(arr)]
    if valid.size == 0:
        return {}
    p02, median, p98 = np.percentile(valid, [2, 50, 98])
    return {
        "min": float(valid.min()),
        "max": float(valid.max()),
        "mean": float(valid.mean()),
        "std": float(valid.std()),
        "p02": float(p02),
        "median": float(median),
        "p98": float(p98),
    }

def spectral_profile(path, row, column, radius=0):
    with rasterio.open(path) as src:
        if row < 0 or row >= src.height or column < 0 or column >= src.width:
            raise ValueError("Pixel is outside the image.")
        r0, r1 = max(0, row - radius), min(src.height, row + radius + 1)
        c0, c1 = max(0, column - radius), min(src.width, column + radius + 1)
        data = src.read(window=Window(c0, r0, c1 - c0, r1 - r0)).astype(np.float32)
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
        if radius == 0:
            return data[:, 0, 0]
        return np.nanmean(data, axis=(1, 2))

def pca_rgb(path, max_dim=220, max_fit_pixels=20_000, random_state=42):
    with rasterio.open(path) as src:
        if src.count < 3:
            raise ValueError("PCA RGB requires at least three bands.")
        h, w = _preview_dimensions(src.width, src.height, max_dim)
        cube = src.read(
            out_shape=(src.count, h, w),
            resampling=Resampling.bilinear,
            out_dtype="float32",
        )
        if src.nodata is not None:
            cube[cube == src.nodata] = np.nan

    x = np.moveaxis(cube, 0, -1).reshape(-1, cube.shape[0])
    valid_mask = np.all(np.isfinite(x), axis=1)
    valid_idx = np.flatnonzero(valid_mask)
    if valid_idx.size < 10:
        raise ValueError("Not enough valid pixels for PCA.")

    rng = np.random.default_rng(random_state)
    fit_idx = (
        rng.choice(valid_idx, size=max_fit_pixels, replace=False)
        if valid_idx.size > max_fit_pixels
        else valid_idx
    )
    model = PCA(n_components=3, svd_solver="randomized", random_state=random_state)
    model.fit(x[fit_idx])

    out_flat = np.full((x.shape[0], 3), np.nan, dtype=np.float32)
    chunk = 50_000
    for start in range(0, valid_idx.size, chunk):
        ids = valid_idx[start : start + chunk]
        out_flat[ids] = model.transform(x[ids]).astype(np.float32)

    output = out_flat.reshape(h, w, 3)
    for component in range(3):
        output[:, :, component] = percentile_stretch(output[:, :, component], 2, 98)
    return output, model.explained_variance_ratio_.astype(np.float32)

def normalized_difference(path, band_a, band_b, max_dim=900):
    with rasterio.open(path) as src:
        h, w = _preview_dimensions(src.width, src.height, max_dim)
        cube = src.read(
            [band_a, band_b],
            out_shape=(2, h, w),
            resampling=Resampling.bilinear,
            out_dtype="float32",
        )
        if src.nodata is not None:
            cube[cube == src.nodata] = np.nan
    return normalized_difference_arrays(cube[0], cube[1])
