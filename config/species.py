from dataclasses import dataclass


@dataclass
class SpeciesConfig:
    name: str
    phase: str
    initial_quantity: float = 0.0
