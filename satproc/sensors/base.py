from dataclasses import dataclass, field

@dataclass(frozen=True)
class SensorInfo:
    name: str
    mission: str
    official_url: str
    data_url: str
    documentation_url: str
    recommended_product: str
    type: str
    supported_levels: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""
