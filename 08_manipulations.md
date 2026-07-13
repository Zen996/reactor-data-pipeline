# Stage 8 — Manipulations

## Context

Mixing (Stage 5), reactions (Stage 6), and physical processes (Stage 7)
give continuous, rule-based dynamics. Real (and realistic-looking
synthetic) process data also has discrete operator/controller
interventions: venting, draining, injecting, removing. This stage adds
that as a fully configurable, trigger-driven process.

## Files to Create

- `processes/manipulation.py`

## Public API

```python
# processes/manipulation.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from core.process import Process

class Trigger(ABC):
    @abstractmethod
    def is_active(self, state) -> bool:
        """Whether the condition holds at the current state/time."""

@dataclass
class TimeTrigger(Trigger):
    time: float
    """Fires (is_active True) once state.time >= self.time. One-shot
    behavior is handled by the Manipulation wrapper, not here — this class
    only reports whether the condition currently holds."""

@dataclass
class ThresholdTrigger(Trigger):
    species: str
    phase: str
    comparator: str   # one of "gt", "lt", "ge", "le"
    value: float

@dataclass
class PeriodicTrigger(Trigger):
    period: float
    phase_offset: float = 0.0
    tolerance: float = 1e-9
    """Active during the instant(s) where (state.time - phase_offset) is
    (approximately) a multiple of period — needs a well-defined "am I on
    the tick" check given discrete dt steps; document exactly how you
    detect this (e.g. compare against the *previous* recorded fire time,
    or check t modulo period falls within one dt of zero)."""

class ManualTrigger(Trigger):
    def __init__(self) -> None: ...
    def fire(self) -> None:
        """External code (e.g. a test, or a future UI) calls this to make
        is_active() return True exactly once."""
    def is_active(self, state) -> bool: ...


class Action(ABC):
    @abstractmethod
    def apply(self, state, dt: float) -> None: ...

@dataclass
class VentVapor(Action):
    species: str | None   # None = vent all vapor species
    fraction: float       # fraction of current quantity removed when applied

@dataclass
class RemoveSpecies(Action):
    phase: str
    species: str
    amount: float

@dataclass
class InjectSpecies(Action):
    phase: str
    species: str
    amount: float

@dataclass
class DrainReactor(Action):
    fraction: float
    """Removes `fraction` of volume and of every liquid species'
    quantity proportionally (keeps concentrations unchanged, only volume
    and absolute quantities shrink)."""


@dataclass
class Manipulation:
    trigger: Trigger
    action: Action
    one_shot: bool = False

class ManipulationProcess(Process):
    def __init__(self, manipulations: list[Manipulation]) -> None: ...
    def execute(self, state, dt: float) -> None: ...
```

## Behavioral Requirements

- `ManipulationProcess.execute` checks every `Manipulation`'s trigger each
  step; if active (and, for `one_shot=True`, not already fired), applies
  its action and — if one-shot — marks it as fired so it never fires
  again for the rest of the run.
- `TimeTrigger.is_active` stays `True` for every step at/after its time
  unless wrapped in `one_shot=True` — this is intentional: a non-one-shot
  time trigger paired with, say, `InjectSpecies` becomes a continuous
  injection from that time onward. Document this clearly since it's a
  meaningful behavioral choice, not an edge case to special-case away.
- `ThresholdTrigger.comparator` must validate to one of the four allowed
  strings; invalid values raise `ValueError` at construction, not
  silently at runtime.
- `PeriodicTrigger` must not fire on every step within a period window —
  pick a precise, testable definition of "on the tick" (e.g., fires when
  `state.time` crosses a period boundary within the current `dt`, checked
  via the previous step's time if available, or via modulo with a
  half-dt tolerance) and write it down.
- Actions never go negative: `RemoveSpecies`/`VentVapor`/`DrainReactor`
  clamp at zero/removing-everything-available rather than under/overflowing.
- `VentVapor(species=None)` applies `fraction` removal to every currently
  registered vapor species.

## Out of Scope

- Any coupling between manipulations and streams (e.g. a manipulation
  toggling `InputStream.set_active` is a natural future extension but not
  required here — note it as an easy follow-on if asked).
- Randomizing trigger thresholds or action amounts (Stage 9).

## Acceptance Criteria

`tests/processes/test_manipulation.py`:

1. `TimeTrigger` + `one_shot=True` + `InjectSpecies`: fires exactly once
   at/after the configured time, never again, across many subsequent
   steps.
2. `TimeTrigger` + `one_shot=False` + `InjectSpecies`: fires every step
   from the configured time onward (verify cumulative injected amount
   grows linearly with elapsed steps past that time).
3. `ThresholdTrigger`: construct a scenario where a species crosses the
   threshold partway through a run (e.g. via a simple synthetic state
   mutation between steps) and verify the manipulation fires only once
   past the crossing point when `one_shot=True`.
4. Invalid `comparator` string raises `ValueError` at construction.
5. `PeriodicTrigger`: over a run of many periods, count firings and verify
   the count matches `duration // period` (within off-by-one tolerance
   you define and test against).
6. `DrainReactor(fraction=0.5)`: volume and every liquid species halve,
   concentrations unchanged.
7. `VentVapor(species=None, fraction=1.0)`: every vapor species goes to
   zero; liquid species untouched.
8. `RemoveSpecies` requesting more than currently available clamps to
   zero rather than going negative.

## Example

`examples/stage_08_demo.py`: a reactor with a one-shot drain at `t=100`
and a periodic small vapor vent every 20 seconds — run through the Stage 1
engine and print volume/vapor species over time showing the sawtooth-like
vent pattern and the single drain event.
