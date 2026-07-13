from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from config.reactions import DecayConfig, EquilibriumConfig, ReactionConfig
from config.species import SpeciesConfig


@dataclass
class StreamConfig:
    name: str
    phase: str
    flow_signal: dict
    composition: dict[str, dict]
    active: bool = True


_MANIPULATION_SPEC = list | dict


@dataclass
class SimulationConfig:
    species: list[SpeciesConfig | dict]
    streams: list[StreamConfig | dict]
    reactions: list[ReactionConfig | dict] = field(default_factory=list)
    decays: list[DecayConfig | dict] = field(default_factory=list)
    equilibria: list[EquilibriumConfig | dict] = field(default_factory=list)
    manipulations: list[_MANIPULATION_SPEC] = field(default_factory=list)
    sensors: list[dict] = field(default_factory=list)
    dt: float = 1.0
    duration: float = 100.0
    seed: int | None = None
    volume: float = 1.0
    outflow_rate: float | dict | None = None
    recorder_output: str | None = None

    @staticmethod
    def from_dict(d: dict) -> "SimulationConfig":
        raw = dict(d)
        raw["species"] = [_to_dataclass(SpeciesConfig, s) for s in raw.get("species", [])]
        raw["streams"] = [_to_dataclass(StreamConfig, s) for s in raw.get("streams", [])]
        raw["reactions"] = [_to_dataclass(ReactionConfig, r) for r in raw.get("reactions", [])]
        raw["decays"] = [_to_dataclass(DecayConfig, d_) for d_ in raw.get("decays", [])]
        raw["equilibria"] = [_to_dataclass(EquilibriumConfig, e) for e in raw.get("equilibria", [])]
        return SimulationConfig(**raw)

    @staticmethod
    def load(path: str) -> "SimulationConfig":
        p = Path(path)
        text = p.read_text(encoding="utf-8")
        if p.suffix in (".yml", ".yaml"):
            import yaml as _yaml

            d = _yaml.safe_load(text)
        elif p.suffix == ".json":
            d = json.loads(text)
        else:
            raise ValueError(f"Unsupported config extension: {p.suffix}")
        return SimulationConfig.from_dict(d)


def _to_dataclass(cls, item):
    if isinstance(item, cls):
        return item
    return cls(**item)
