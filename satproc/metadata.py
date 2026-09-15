from __future__ import annotations

from .models import RasterCube


def summarize_metadata(cube: RasterCube) -> dict:
    shape = cube.data.shape
    return {
        "source_path": cube.source_path,
        "bands": int(shape[0]),
        "height": int(shape[1]),
        "width": int(shape[2]),
        "dtype": str(cube.data.dtype),
        "crs": str(cube.profile.get("crs")),
        "transform": str(cube.profile.get("transform")),
        "driver": cube.profile.get("driver"),
        "wavelength_count": len(cube.wavelengths_nm),
        **cube.metadata,
    }
