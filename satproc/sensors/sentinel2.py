from .base import SensorInfo

SENTINEL2 = SensorInfo(
    name="Sentinel-2",
    mission="Copernicus Sentinel-2",
    official_url="https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-2",
    data_url="https://browser.dataspace.copernicus.eu/",
    documentation_url="https://documentation.dataspace.copernicus.eu/",
    recommended_product="Level-2A",
    type="Multispectral",
    supported_levels=("L1C", "L2A"),
    notes=(
        "Level-2A surface reflectance is recommended for many terrestrial analyses. "
        "Individual band files are supported; not every product is a single multiband raster."
    ),
)
