from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio

from .models import DatasetLoadError, RasterCube


def _read_raster(path: Path) -> RasterCube:
    try:
        with rasterio.open(path) as src:
            data = src.read().astype(np.float32)
            profile = src.profile.copy()
            tags = src.tags().copy()
            wavelengths = []
            if "wavelength" in tags:
                wavelengths = [float(x) for x in str(tags["wavelength"]).replace("{", "").replace("}", "").split(",") if x.strip()]
        return RasterCube(
            data=data,
            profile=profile,
            wavelengths_nm=wavelengths,
            metadata={"tags": tags},
            source_path=str(path),
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise DatasetLoadError(f"Unable to read raster file: {path}. {exc}") from exc


def load_dataset(path: str | Path) -> RasterCube:
    from .sensors.enmap import load_enmap_cube

    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise DatasetLoadError(f"Path does not exist: {p}")

    looks_like_enmap = p.is_dir() or p.name.upper() == "METADATA.XML"
    if looks_like_enmap:
        try:
            return load_enmap_cube(p)
        except Exception as exc:
            raise DatasetLoadError(str(exc)) from exc

    if p.suffix.lower() in {".hdr", ".bsq", ".bil", ".bip"}:
        try:
            return load_enmap_cube(p)
        except Exception:
            pass

    return _read_raster(p)
