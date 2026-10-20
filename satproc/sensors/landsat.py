from .base import SensorInfo

LANDSAT = SensorInfo(
    name="Landsat",
    mission="Landsat 8 / Landsat 9",
    official_url="https://www.usgs.gov/landsat-missions",
    data_url="https://earthexplorer.usgs.gov/",
    documentation_url="https://www.usgs.gov/landsat-missions/landsat-data-access",
    recommended_product="Collection 2 Level-2",
    type="Multispectral + Thermal",
    supported_levels=("Collection 2 Level-1", "Collection 2 Level-2"),
    notes=(
        "Collection 2 Level-2 is recommended for many surface-reflectance workflows. "
        "Thermal bands should not be treated as reflectance bands."
    ),
)
