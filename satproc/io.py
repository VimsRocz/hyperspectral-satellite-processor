\
from pathlib import Path
import re
import zipfile
import rasterio

RASTER_EXTENSIONS = {
    ".tif", ".tiff", ".jp2", ".img", ".dat", ".bil", ".bsq", ".bip"
}

def safe_extract_zip(zip_path: Path, destination: Path):
    destination = destination.resolve()
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            target = (destination / member.filename).resolve()
            if str(target).startswith(str(destination)):
                zf.extract(member, destination)

def save_uploaded_files(uploaded_files, destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    for uploaded in uploaded_files:
        output = destination / Path(uploaded.name).name
        with open(output, "wb") as f:
            f.write(uploaded.getbuffer())

        if output.suffix.lower() == ".zip":
            extract_dir = destination / output.stem
            extract_dir.mkdir(exist_ok=True)
            try:
                safe_extract_zip(output, extract_dir)
            except Exception:
                pass

def _can_open(path: Path):
    try:
        with rasterio.open(path):
            return True
    except Exception:
        return False

def discover_rasters(root):
    root = Path(root).expanduser()
    if root.is_file():
        if root.suffix.lower() in RASTER_EXTENSIONS and _can_open(root):
            return [root]
        return []

    if not root.exists():
        return []

    candidates = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in RASTER_EXTENSIONS and _can_open(p):
            candidates.append(p)
    return sorted(candidates)

def _parse_numbers(value):
    if value is None:
        return []
    pattern = r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?"
    return [float(x) for x in re.findall(pattern, str(value))]

def get_wavelengths(path):
    with rasterio.open(path) as src:
        count = src.count
        metadata_sets = [src.tags()]
        try:
            metadata_sets.append(src.tags(ns="ENVI"))
        except Exception:
            pass

        likely_keys = {
            "wavelength", "wavelengths", "band_wavelength",
            "band_wavelengths", "central_wavelength", "central_wavelengths"
        }

        for metadata in metadata_sets:
            for key, value in metadata.items():
                if key.lower() in likely_keys:
                    values = _parse_numbers(value)
                    if len(values) >= count:
                        return values[:count]

        wavelengths = []
        for band in range(1, count + 1):
            tags = src.tags(band)
            found = None
            for key, value in tags.items():
                if "wavelength" in key.lower():
                    nums = _parse_numbers(value)
                    if nums:
                        found = nums[0]
                        break
            if found is None:
                wavelengths = []
                break
            wavelengths.append(found)

        return wavelengths if len(wavelengths) == count else None

def get_band_labels(path):
    with rasterio.open(path) as src:
        labels = []
        for i in range(src.count):
            labels.append(src.descriptions[i] or f"Band {i + 1}")
        return labels

def guess_sensor(path, src):
    filename = Path(path).name.lower()
    metadata_text = " ".join(f"{k}={v}" for k, v in src.tags().items()).lower()
    combined = filename + " " + metadata_text

    if "enmap" in combined:
        return "EnMAP"
    if any(x in combined for x in ["sentinel", "s2a", "s2b", "msil1c", "msil2a"]):
        return "Sentinel-2"
    if any(x in combined for x in ["landsat", "lc08", "lc09", "le07", "lt05"]):
        return "Landsat"
    return "Unknown / Generic"

def guess_image_type(path, src):
    sensor = guess_sensor(path, src)
    bands = src.count
    if bands >= 20:
        return "Hyperspectral / high-dimensional spectral raster"
    if bands > 1:
        return "Multispectral / multiband raster"
    if sensor in {"Sentinel-2", "Landsat"}:
        return "Multispectral dataset — this file contains one band"
    return "Single-band raster"

def inspect_raster(path):
    path = Path(path)
    with rasterio.open(path) as src:
        info = {
            "file": path.name,
            "sensor_guess": guess_sensor(path, src),
            "image_type_guess": guess_image_type(path, src),
            "driver": src.driver,
            "bands": src.count,
            "width": src.width,
            "height": src.height,
            "dtype": str(src.dtypes[0]),
            "crs": str(src.crs),
            "nodata": src.nodata,
            "bounds": str(src.bounds),
            "transform": str(src.transform),
        }
        tags = src.tags()
    return info, tags
