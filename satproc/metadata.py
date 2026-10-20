from __future__ import annotations
from pathlib import Path
import re
import rasterio

WAVELENGTH_KEYS = {
    "wavelength",
    "wavelengths",
    "band_wavelength",
    "band_wavelengths",
    "central_wavelength",
    "central_wavelengths",
}

def parse_numbers(value) -> list[float]:
    if value is None:
        return []
    pattern = r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?"
    return [float(x) for x in re.findall(pattern, str(value))]

def detect_product_level(path: str | Path) -> str:
    text = str(path).upper()
    for level in ("L2A", "L1C", "L1B"):
        if level in text:
            return level
    if "MSIL2A" in text:
        return "L2A"
    if "MSIL1C" in text:
        return "L1C"
    if "COLLECTION 2 LEVEL-2" in text or "_L2_" in text:
        return "Collection 2 Level-2"
    return "Unknown"

def classify_file_role(path: str | Path) -> str:
    name = Path(path).name.upper()
    if "SPECTRAL_IMAGE" in name:
        return "science_image"
    if "QL_PIXELMASK" in name or "QL_QUALITY_" in name:
        return "quality_mask"
    if "QL_VNIR" in name or "QL_SWIR" in name or "QUICKLOOK" in name:
        return "quicklook"
    if Path(path).suffix.lower() in {".xml", ".hdr"}:
        return "metadata"
    return "unknown_raster"

def quantity_for(sensor: str, product_level: str) -> str:
    if sensor == "EnMAP":
        if product_level == "L2A":
            return "Surface reflectance"
        if product_level in {"L1B", "L1C"}:
            return "Radiance-oriented product"
    if sensor == "Sentinel-2" and product_level == "L2A":
        return "Surface reflectance"
    if sensor == "Landsat" and "Level-2" in product_level:
        return "Surface reflectance / thermal science products"
    return "Unknown / sensor-dependent"

def find_nearest_band(wavelengths: list[float] | tuple[float, ...], target_nm: float) -> tuple[int, float]:
    if not wavelengths:
        raise ValueError("No wavelength metadata is available.")
    idx = min(range(len(wavelengths)), key=lambda i: abs(wavelengths[i] - target_nm))
    return idx + 1, float(wavelengths[idx])

def extract_static_metadata(path: str | Path) -> dict:
    path = Path(path)
    with rasterio.open(path) as src:
        tags = src.tags()
        envi_tags = {}
        try:
            envi_tags = src.tags(ns="ENVI")
        except Exception:
            pass

        metadata_sets = (tags, envi_tags)
        wavelengths = None
        for metadata in metadata_sets:
            for key, value in metadata.items():
                if key.lower() in WAVELENGTH_KEYS:
                    values = parse_numbers(value)
                    if len(values) >= src.count:
                        wavelengths = values[: src.count]
                        break
            if wavelengths:
                break

        labels = [d or f"Band {i + 1}" for i, d in enumerate(src.descriptions)]
        return {
            "driver": src.driver,
            "bands": src.count,
            "width": src.width,
            "height": src.height,
            "dtype": str(src.dtypes[0]),
            "crs": str(src.crs),
            "nodata": src.nodata,
            "bounds": str(src.bounds),
            "transform": str(src.transform),
            "tags": tags,
            "band_labels": labels,
            "wavelengths": wavelengths,
        }
