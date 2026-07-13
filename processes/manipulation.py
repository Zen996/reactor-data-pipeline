"""Event-driven operator interventions: vent, drain, inject, remove.

Triggers define *when* an action happens; actions define *what* happens.
A :class:`Manipulation` pairs one trigger with one action and an optional
one-shot flag.

All actions clamp at zero — they never drive a species or volume negative.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from core.process import Process


# ── Triggers ──────────────────────────────────────────────────────────


class Trigger(ABC):
    """Decides whether a manipulation's action should fire this step."""

    @abstractmethod
    def is_active(self, state) -> bool:
        ...


@dataclass
class TimeTrigger(Trigger):
    """Fires for every step where ``state.time >= self.time``.

    When paired with ``one_shot=True`` on the :class:`Manipulation`, the
    manipulation fires only once.  With ``one_shot=False`` (default) it
    becomes a continuous effect from *time* onward (e.g. a continuous
    injection).
    """

    time: float

    def is_active(self, state) -> bool:
        return state.time >= self.time


_VALID_COMPARATORS = ("gt", "lt", "ge", "le")


@dataclass
class ThresholdTrigger(Trigger):
    """Fires when the species' concentration crosses the threshold.

    *comparator* must be one of ``"gt"``, ``"lt"``, ``"ge"``, ``"le"``.
    Raises ``ValueError`` at construction if invalid.
    """

    species: str
    phase: str
    comparator: str
    value: float

    def __post_init__(self) -> None:
        if self.comparator not in _VALID_COMPARATORS:
            raise ValueError(
                f"Invalid comparator {self.comparator!r}; "
                f"must be one of {_VALID_COMPARATORS}"
            )

    def is_active(self, state) -> bool:
        try:
            conc = state.concentration(self.species, phase=self.phase)
        except KeyError:
            return False
        if self.comparator == "gt":
            return conc > self.value
        elif self.comparator == "lt":
            return conc < self.value
        elif self.comparator == "ge":
            return conc >= self.value
        elif self.comparator == "le":
            return conc <= self.value
        return False


@dataclass
class PeriodicTrigger(Trigger):
    """Fires once per period, when ``state.time`` crosses a period boundary.

    Detection: fires when ``state.time - self._last_fire >= period``,
    using an internal ``_last_fire`` tracker initialised to ``-inf`` so
    the first tick is always ``phase_offset``.

    ``phase_offset`` shifts the first fire time (e.g. first fire at
    ``phase_offset``, then every ``period`` thereafter).
    """

    period: float
    phase_offset: float = 0.0
    _last_fire: float = field(default=-float("inf"), repr=False, compare=False)

    def is_active(self, state) -> bool:
        if state.time - self._last_fire >= self.period - 1e-12:
            if state.time >= self.phase_offset:
                self._last_fire = state.time
                return True
        return False


class ManualTrigger(Trigger):
    """Fires exactly once each time ``.fire()`` is called from external
    code (tests, UI, etc.), then returns ``False`` until called again."""

    def __init__(self) -> None:
        self._pending: bool = False

    def fire(self) -> None:
        self._pending = True

    def is_active(self, state) -> bool:
        if self._pending:
            self._pending = False
            return True
        return False


# ── Actions ────────────────────────────────────────────────────────────


class Action(ABC):
    """A discrete change applied to reactor state."""

    @abstractmethod
    def apply(self, state, dt: float) -> None:
        ...


@dataclass
class VentVapor(Action):
    """Remove a fraction of a vapor species (or all vapor species).

    If *species* is ``None``, the fraction is applied to every species
    currently registered in the vapor phase.
    """

    species: str | None
    fraction: float

    def apply(self, state, dt: float) -> None:
        if self.fraction <= 0.0:
            return
        if self.species is None:
            targets = list(state.vapor.keys())
        else:
            targets = [self.species] if self.species in state.vapor else []

        for sp in targets:
            qty = state.vapor[sp]
            removed = qty * self.fraction
            if removed > qty:
                removed = qty
            state.add(sp, -removed, phase="vapor")


@dataclass
class RemoveSpecies(Action):
    """Remove a fixed amount of a species from a phase.

    Clamps at zero if amount exceeds the current quantity available.
    """

    phase: str
    species: str
    amount: float

    def apply(self, state, dt: float) -> None:
        if self.amount <= 0.0:
            return
        try:
            qty = state.get(self.species, phase=self.phase)
        except KeyError:
            return
        removed = min(self.amount, qty)
        state.add(self.species, -removed, phase=self.phase)


@dataclass
class InjectSpecies(Action):
    """Add a fixed amount of a species to a phase."""

    phase: str
    species: str
    amount: float

    def apply(self, state, dt: float) -> None:
        if self.amount <= 0.0:
            return
        state.add(self.species, self.amount, phase=self.phase)


@dataclass
class DrainReactor(Action):
    """Remove a fraction of the reactor's volume and every liquid
    species proportionally, keeping concentrations unchanged."""

    fraction: float

    def apply(self, state, dt: float) -> None:
        if self.fraction <= 0.0:
            return
        f = min(self.fraction, 1.0)
        for sp in list(state.liquid.keys()):
            qty = state.liquid[sp]
            removed = qty * f
            state.add(sp, -removed, phase="liquid")
        state.volume *= 1.0 - f


# ── Manipulation & Process ────────────────────────────────────────────


@dataclass
class Manipulation:
    """Pairs a trigger with an action.

    Parameters
    ----------
    trigger:
        When to fire.
    action:
        What to do.
    one_shot:
        If ``True``, the manipulation fires at most once per run.
    fired_at:
        Sim time at which this manipulation last fired (None = hasn't fired).
        Used for rewind-aware one-shot tracking.
    """

    trigger: Trigger
    action: Action
    one_shot: bool = False
    fired_at: float | None = None


class ManipulationProcess(Process):
    """Check every :class:`Manipulation` each step and apply active ones."""

    def __init__(self, manipulations: list[Manipulation]) -> None:
        self._manipulations = list(manipulations)

    def execute(self, state, dt: float) -> None:
        for i, m in enumerate(self._manipulations):
            if m.one_shot and m.fired_at is not None:
                continue
            if m.trigger.is_active(state):
                m.action.apply(state, dt)
                if m.one_shot:
                    m.fired_at = state.time
                    state.derived.setdefault("manipulations", []).append(
                        {
                            "time": state.time,
                            "index": i,
                            "trigger": type(m.trigger).__name__,
                            "action": type(m.action).__name__,
                        }
                    )
