"""Reactor state data model — pure data, no domain logic."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field


_VALID_PHASES = ("liquid", "vapor")


@dataclass
class ReactorState:
    """Complete reactor state at a single instant in time.

    Species are stored as dict keys — no hardcoded species names anywhere.
    ``liquid`` and ``vapor`` are the two phase dicts. ``inflows`` tracks
    the last-step aggregated species inflow rates (for recording, not
    included in ``snapshot()``). ``derived`` is scratch space for computed
    quantities like reaction rates or measured values. ``metadata`` holds
    static run info (species list, units, run id, …) and is excluded from
    ``snapshot()``.

    .. note::

        Negative values are **not** clamped here — that is a per-process
        responsibility (reactions / decay should clamp to avoid going
        below zero; mixing may not need to).
    """

    time: float = 0.0
    volume: float = 1.0
    liquid: dict[str, float] = field(default_factory=dict)
    vapor: dict[str, float] = field(default_factory=dict)
    inflows: dict[str, float] = field(default_factory=dict)
    outflow_rate: float = 0.0
    derived: dict[str, float] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    # --- species accessors -------------------------------------------------

    def _validate_phase(self, phase: str) -> None:
        if phase not in _VALID_PHASES:
            raise ValueError(
                f"Invalid phase {phase!r}; must be one of {_VALID_PHASES}"
            )

    def _phase_dict(self, phase: str) -> dict[str, float]:
        self._validate_phase(phase)
        return self.liquid if phase == "liquid" else self.vapor

    def get(self, species: str, phase: str = "liquid") -> float:
        """Return the quantity of *species* in *phase*.

        Raises ``KeyError`` if the species has not been registered (a
        silent zero would hide config mistakes).
        """
        d = self._phase_dict(phase)
        try:
            return d[species]
        except KeyError:
            raise KeyError(
                f"Species {species!r} not found in {phase} phase. "
                f"Call register_species() first."
            ) from None

    def set(self, species: str, value: float, phase: str = "liquid") -> None:
        """Set *species* to *value*. Intended for initialisation / tests."""
        self.get(species, phase)  # raises if unregistered
        self._phase_dict(phase)[species] = value

    def add(self, species: str, delta: float, phase: str = "liquid") -> None:
        """Add *delta* to *species*. Standard way processes mutate state.

        Does **not** clamp negative values — that is a per-process
        decision.
        """
        self.get(species, phase)  # raises if unregistered
        self._phase_dict(phase)[species] += delta

    def concentration(self, species: str, phase: str = "liquid") -> float:
        """Quantity of *species* divided by current volume.

        Vapor concentration uses the same ``volume`` field unless a
        separate headspace volume is introduced (TODO: future extension).
        """
        return self.get(species, phase) / self.volume

    # --- species lifecycle -------------------------------------------------

    def register_species(
        self, name: str, phase: str = "liquid", initial: float = 0.0
    ) -> None:
        """Explicitly add a new species with an optional starting value."""
        self._validate_phase(phase)
        if phase == "liquid":
            self.liquid[name] = initial
        else:
            self.vapor[name] = initial

    # --- bulk queries -----------------------------------------------------

    def total_mass(self, phase: str | None = None) -> float:
        """Sum of quantities in one phase, or both if *phase* is ``None``."""
        if phase is None:
            return sum(self.liquid.values()) + sum(self.vapor.values())
        return sum(self._phase_dict(phase).values())

    def snapshot(self) -> dict:
        """Flatten the state into a single-level dict for one tabular row.

        Keys follow the pattern: ``liquid.<name>``, ``vapor.<name>``,
        ``derived.<key>``, plus top-level ``time``, ``volume``,
        ``outflow_rate``.

        ``metadata`` (static run info) and ``inflows`` (last-step rates)
        are excluded — they belong in a separate run-level record.
        """
        row: dict = {
            "time": self.time,
            "volume": self.volume,
            "outflow_rate": self.outflow_rate,
        }
        for name, qty in self.liquid.items():
            row[f"liquid.{name}"] = qty
            row[f"conc.{name}"] = qty / self.volume if self.volume > 0 else 0.0
        for name, qty in self.vapor.items():
            row[f"vapor.{name}"] = qty
        for key, val in self.derived.items():
            row[f"derived.{key}"] = val
        return row

    def copy(self) -> "ReactorState":
        """Deep copy, safe for before/after comparison in tests."""
        return copy.deepcopy(self)
