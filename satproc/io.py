from __future__ import annotations

from pathlib import Path
import tempfile
import zipfile
import rasterio

from .metadata import (
    classify_file_role,
    detect_product_level,
    extract_static_metadata,
    quantity_for,
)

RASTER_EXTENSIONS = {
    ".tif", ".tiff", ".jp2", ".img", ".dat", ".bil", ".bsq", ".bip"
}
SAFE_AUX_EXTENSIONS = {".hdr", ".xml"}
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 4 * 1024 * 1024 * 1024

def normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()

def file_signature(path: str | Path) -> tuple[str, int, int]:
    p = normalize_path(path)
    stat = p.stat()
    return str(p), int(stat.st_size), int(stat.st_mtime_ns)

def directory_signature(root: str | Path) -> tuple[str, int, int]:
    """Cheap cache signature.

    Directory mtime changes when direct children are added/removed/renamed.
    This avoids recursively stat'ing every product file on each Streamlit rerun.
    Use the manual cache-clear control if deeply nested files are modified in place.
    """
    root = normalize_path(root)
    stat = root.stat()
    kind = 1 if root.is_file() else 0
    return str(root), kind, int(stat.st_mtime_ns)

def safe_extract_zip(zip_path: Path, destination: Path, max_uncompressed_bytes: int = MAX_ARCHIVE_UNCOMPRESSED_BYTES):
    destination = destination.resolve()
    total = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = []
        for member in zf.infolist():
            suffix = Path(member.filename).suffix.lower()
            if suffix not in (RASTER_EXTENSIONS | SAFE_AUX_EXTENSIONS | {".txt", ".json"}):
                continue
            total += member.file_size
            if total > max_uncompressed_bytes:
                raise ValueError("Archive is too large after decompression.")
            target = (destination / member.filename).resolve()
            if not str(target).startswith(str(destination)):
                raise ValueError("Unsafe archive path detected.")
            members.append(member)
        for member in members:
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
            safe_extract_zip(output, extract_dir)

def make_upload_tempdir() -> Path:
    return Path(tempfile.mkdtemp(prefix="satellite_processor_"))

def _can_open(path: Path) -> bool:
    try:
        with rasterio.open(path):
            return True
    except Exception:
        return False

def discover_rasters(root: str | Path) -> list[Path]:
    root = normalize_path(root)
    if root.is_file():
        return [root] if root.suffix.lower() in RASTER_EXTENSIONS and _can_open(root) else []
    if not root.exists():
        return []

    science, other = [], []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in RASTER_EXTENSIONS:
            continue
        role = classify_file_role(p)
        if not _can_open(p):
            continue
        if role == "science_image":
            science.append(p)
        else:
            other.append(p)
    return sorted(science) + sorted(other)

def guess_sensor(path: str | Path, tags: dict | None = None) -> str:
    p = Path(path)
    combined = (str(p) + " " + " ".join(f"{k}={v}" for k, v in (tags or {}).items())).lower()
    if "enmap" in combined:
        return "EnMAP"
    if any(x in combined for x in ("sentinel", "s2a", "s2b", "msil1c", "msil2a")):
        return "Sentinel-2"
    if any(x in combined for x in ("landsat", "lc08", "lc09", "le07", "lt05")):
        return "Landsat"
    return "Unknown / Generic"

def guess_image_type(sensor: str, bands: int, role: str) -> str:
    if role in {"quality_mask", "quicklook"}:
        return role.replace("_", " ").title()
    if sensor == "EnMAP" and bands >= 20:
        return "Hyperspectral"
    if bands >= 20:
        return "Hyperspectral / high-dimensional raster"
    if bands > 1:
        return "Multispectral / multiband raster"
    if sensor in {"Sentinel-2", "Landsat"}:
        return "Single band from multispectral product"
    return "Single-band raster"

def inspect_raster(path: str | Path) -> tuple[dict, dict]:
    p = normalize_path(path)
    meta = extract_static_metadata(p)
    sensor = guess_sensor(p, meta["tags"])
    level = detect_product_level(p)
    role = classify_file_role(p)
    info = {
        "file": p.name,
        "sensor_guess": sensor,
        "product_level": level,
        "file_role": role,
        "data_quantity": quantity_for(sensor, level),
        "image_type_guess": guess_image_type(sensor, meta["bands"], role),
        "driver": meta["driver"],
        "bands": meta["bands"],
        "width": meta["width"],
        "height": meta["height"],
        "dtype": meta["dtype"],
        "crs": meta["crs"],
        "nodata": meta["nodata"],
        "bounds": meta["bounds"],
        "transform": meta["transform"],
    }
    return info, meta["tags"]

def get_wavelengths(path: str | Path):
    return extract_static_metadata(path)["wavelengths"]

def get_band_labels(path: str | Path):
    return extract_static_metadata(path)["band_labels"]
