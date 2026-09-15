\
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window
from sklearn.decomposition import PCA

def _preview_dimensions(width, height, max_dim=900):
    scale = min(max_dim / width, max_dim / height, 1.0)
    return max(1, int(height * scale)), max(1, int(width * scale))

def _replace_nodata(data, nodata):
    data = data.astype(np.float32)
    if nodata is not None:
        data[data == nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data

def percentile_stretch(array, low=2, high=98):
    arr = array.astype(np.float32)
    valid = arr[np.isfinite(arr)]
    if valid.size == 0:
        return np.zeros_like(arr, dtype=np.float32)
    minimum = np.percentile(valid, low)
    maximum = np.percentile(valid, high)
    if maximum <= minimum:
        return np.zeros_like(arr, dtype=np.float32)
    output = (arr - minimum) / (maximum - minimum)
    output = np.clip(output, 0, 1)
    output[~np.isfinite(output)] = 0
    return output.astype(np.float32)

def read_band_preview(path, band=1, max_dim=900):
    with rasterio.open(path) as src:
        h, w = _preview_dimensions(src.width, src.height, max_dim)
        data = src.read(
            band, out_shape=(h, w), resampling=Resampling.bilinear
        )
        return _replace_nodata(data, src.nodata)

def read_rgb_preview(path, red_band, green_band, blue_band, low=2, high=98, max_dim=900):
    with rasterio.open(path) as src:
        h, w = _preview_dimensions(src.width, src.height, max_dim)
        bands = []
        for band_number in [red_band, green_band, blue_band]:
            arr = src.read(
                band_number, out_shape=(h, w), resampling=Resampling.bilinear
            )
            arr = _replace_nodata(arr, src.nodata)
            bands.append(percentile_stretch(arr, low, high))
    return np.clip(np.dstack(bands), 0, 1)

def read_rgb_files(red_path, green_path, blue_path, low=2, high=98, max_dim=900):
    paths = [red_path, green_path, blue_path]
    with rasterio.open(paths[0]) as ref:
        h, w = _preview_dimensions(ref.width, ref.height, max_dim)

    result = []
    for path in paths:
        with rasterio.open(path) as src:
            arr = src.read(
                1, out_shape=(h, w), resampling=Resampling.bilinear
            )
            arr = _replace_nodata(arr, src.nodata)
            result.append(percentile_stretch(arr, low, high))
    return np.clip(np.dstack(result), 0, 1)

def calculate_stats(path, band=1):
    arr = read_band_preview(path, band=band, max_dim=600)
    valid = arr[np.isfinite(arr)]
    if valid.size == 0:
        return {}
    return {
        "min": float(np.min(valid)),
        "max": float(np.max(valid)),
        "mean": float(np.mean(valid)),
        "std": float(np.std(valid)),
        "p02": float(np.percentile(valid, 2)),
        "median": float(np.median(valid)),
        "p98": float(np.percentile(valid, 98)),
    }

def spectral_profile(path, row, column):
    with rasterio.open(path) as src:
        if row < 0 or row >= src.height or column < 0 or column >= src.width:
            raise ValueError("Pixel is outside the image.")
        pixel = src.read(window=Window(column, row, 1, 1))
        values = pixel[:, 0, 0].astype(np.float32)
        if src.nodata is not None:
            values[values == src.nodata] = np.nan
    return values

def pca_rgb(path, max_dim=220):
    with rasterio.open(path) as src:
        if src.count < 3:
            raise ValueError("PCA RGB requires at least three bands.")
        h, w = _preview_dimensions(src.width, src.height, max_dim)
        cube = src.read(
            out_shape=(src.count, h, w),
            resampling=Resampling.bilinear,
        ).astype(np.float32)
        if src.nodata is not None:
            cube[cube == src.nodata] = np.nan

    X = np.moveaxis(cube, 0, -1).reshape(-1, cube.shape[0])
    valid_mask = np.all(np.isfinite(X), axis=1)
    X_valid = X[valid_mask]
    if X_valid.shape[0] < 10:
        raise ValueError("Not enough valid pixels for PCA.")

    model = PCA(n_components=3, svd_solver="randomized", random_state=42)
    transformed = model.fit_transform(X_valid)

    output = np.full((X.shape[0], 3), np.nan, dtype=np.float32)
    output[valid_mask] = transformed
    output = output.reshape(h, w, 3)

    for component in range(3):
        output[:, :, component] = percentile_stretch(
            output[:, :, component], 2, 98
        )

    return output, model.explained_variance_ratio_

def normalized_difference(path, band_a, band_b, max_dim=900):
    with rasterio.open(path) as src:
        h, w = _preview_dimensions(src.width, src.height, max_dim)
        a = src.read(
            band_a, out_shape=(h, w), resampling=Resampling.bilinear
        ).astype(np.float32)
        b = src.read(
            band_b, out_shape=(h, w), resampling=Resampling.bilinear
        ).astype(np.float32)
        if src.nodata is not None:
            a[a == src.nodata] = np.nan
            b[b == src.nodata] = np.nan

    with np.errstate(divide="ignore", invalid="ignore"):
        result = (a - b) / (a + b)
    result[~np.isfinite(result)] = np.nan
    return result
