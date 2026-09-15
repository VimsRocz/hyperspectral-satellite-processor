from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class RasterCube:
    data: np.ndarray  # (bands, rows, cols)
    profile: dict[str, Any]
    wavelengths_nm: list[float]
    metadata: dict[str, Any]
    source_path: str


class DatasetLoadError(RuntimeError):
    pass
