from .base import SensorInfo
from .enmap import ENMAP
from .sentinel2 import SENTINEL2
from .landsat import LANDSAT

SENSORS = {
    "EnMAP": ENMAP,
    "Sentinel-2": SENTINEL2,
    "Landsat": LANDSAT,
}

def get_sensor_info(name: str) -> SensorInfo | None:
    return SENSORS.get(name)
