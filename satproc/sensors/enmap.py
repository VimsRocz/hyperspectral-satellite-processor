from .base import SensorInfo

ENMAP = SensorInfo(
    name="EnMAP",
    mission="Environmental Mapping and Analysis Program",
    official_url="https://www.enmap.org/",
    data_url="https://www.enmap.org/data_access/",
    documentation_url="https://www.enmap.org/data_tools/exampledata/",
    recommended_product="L2A",
    type="Hyperspectral",
    supported_levels=("L1B", "L1C", "L2A"),
    notes=(
        "L1B may provide VNIR and SWIR as separate radiance-oriented cubes. "
        "L1C is geometrically corrected/orthorectified. "
        "L2A is the preferred starting point for surface-reflectance analysis."
    ),
)
