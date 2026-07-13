from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReactionConfig:
    reactants: dict[str, int]
    products: dict[str, int]
    rate_constant: float | dict
    order: dict[str, float] | None = None
    phase: str = "liquid"


@dataclass
class DecayConfig:
    species: str
    rate_constant: float | dict
    phase: str = "liquid"
    products: dict[str, int] | None = None


@dataclass
class EquilibriumConfig:
    species: str
    evaporation_coeff: float
    condensation_coeff: float
