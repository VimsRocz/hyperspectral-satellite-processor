from __future__ import annotations

import re
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

import numpy as np
import rasterio

from satproc.models import DatasetLoadError, RasterCube


def _find_root(path: Path) -> Path:
    if path.is_dir():
        return path
    return path.parent


def detect_product_level(path: Path) -> str:
    s = str(path).upper()
    for level in ("L1B", "L1C", "L2A"):
        if level in s:
            return level

    metadata_xml = next(iter(path.rglob("*METADATA.XML")), None) if path.is_dir() else None
    if metadata_xml:
        txt = metadata_xml.read_text(encoding="utf-8", errors="ignore").upper()
        for level in ("L1B", "L1C", "L2A"):
            if level in txt:
                return level
    return "UNKNOWN"


def find_metadata_xml(root: Path) -> Path | None:
    candidates = list(root.rglob("*METADATA.XML"))
    return candidates[0] if candidates else None


def _is_spectral_candidate(p: Path) -> bool:
    name = p.name.upper()
    if "QL_PIXELMASK" in name or "QL_QUALITY" in name:
        return False
    return "SPECTRAL_IMAGE" in name


def find_spectral_images(root: Path) -> dict[str, Path]:
    files = [p for p in root.rglob("*") if p.is_file() and _is_spectral_candidate(p)]
    out: dict[str, Path] = {}
    for f in files:
        up = f.name.upper()
        if "VNIR" in up:
            out["VNIR"] = f
        elif "SWIR" in up:
            out["SWIR"] = f
    if not out and files:
        # fallback: one untagged spectral image
        out["SPECTRAL"] = files[0]
    return out


def parse_envi_wavelengths_from_hdr(hdr_path: Path) -> list[float]:
    txt = hdr_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"wavelength\s*=\s*\{([^}]*)\}", txt, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if not m:
        return []
    vals = [x.strip() for x in m.group(1).replace("\n", " ").split(",")]
    out = []
    for v in vals:
        if v:
            try:
                out.append(float(v))
            except ValueError:
                pass
    return out


def parse_wavelengths_from_metadata_xml(xml_path: Path) -> list[float]:
    try:
        root = ET.parse(xml_path).getroot()
    except Exception:
        return []

    vals: list[float] = []
    for elem in root.iter():
        tag = elem.tag.upper()
        text = (elem.text or "").strip()
        if "WAVELENGTH" in tag and text:
            for token in re.split(r"[\s,;]+", text):
                try:
                    vals.append(float(token))
                except ValueError:
                    continue
    return vals


def _try_find_hdr_for_image(image_path: Path) -> Path | None:
    siblings = [
        image_path.with_suffix(image_path.suffix + ".hdr"),
        image_path.with_suffix(".hdr"),
        image_path.parent / f"{image_path.stem}.hdr",
    ]
    for p in siblings:
        if p.exists():
            return p
    return None


def _read_image(path: Path) -> tuple[np.ndarray, dict[str, Any], dict[str, str]]:
    with rasterio.open(path) as src:
        return src.read().astype(np.float32), src.profile.copy(), src.tags().copy()


def _fit_wavelengths_to_band_count(wavelengths: list[float], band_count: int) -> list[float]:
    if len(wavelengths) == band_count:
        return wavelengths
    if len(wavelengths) > band_count:
        return wavelengths[:band_count]
    return [float("nan")] * band_count


def load_enmap_cube(path: Path) -> RasterCube:
    root = _find_root(path)
    spectral = find_spectral_images(root)
    metadata_xml = find_metadata_xml(root)

    if not spectral:
        raise DatasetLoadError(
            f"No EnMAP spectral image found under: {root}. Expected files containing SPECTRAL_IMAGE and excluding QL_PIXELMASK/QL_QUALITY."
        )

    bands_data = []
    all_waves: list[float] = []
    base_profile: dict[str, Any] = {}

    for key in ("VNIR", "SWIR", "SPECTRAL"):
        image = spectral.get(key)
        if image is None:
            continue
        data, profile, tags = _read_image(image)
        if not base_profile:
            base_profile = profile
        bands_data.append(data)

        hdr = _try_find_hdr_for_image(image)
        waves = parse_envi_wavelengths_from_hdr(hdr) if hdr else []
        if not waves and metadata_xml:
            waves = parse_wavelengths_from_metadata_xml(metadata_xml)
        all_waves.extend(_fit_wavelengths_to_band_count(waves, data.shape[0]))

    if not bands_data:
        raise DatasetLoadError(f"No readable EnMAP spectral image bands found in {root}")

    merged = np.concatenate(bands_data, axis=0)

    metadata = {
        "sensor": "EnMAP",
        "product_level": detect_product_level(root),
        "spectral_files": {k: str(v) for k, v in spectral.items()},
        "metadata_xml": str(metadata_xml) if metadata_xml else None,
    }

    return RasterCube(
        data=merged,
        profile=base_profile,
        wavelengths_nm=all_waves,
        metadata=metadata,
        source_path=str(root),
    )
