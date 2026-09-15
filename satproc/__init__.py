"""satproc package for local hyperspectral and multispectral processing."""

from .io import load_dataset
from .models import RasterCube

__all__ = ["RasterCube", "load_dataset"]
