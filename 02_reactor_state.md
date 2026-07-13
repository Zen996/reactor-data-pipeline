# Stage 2 — Reactor State

## Context

Stage 1 gave you `SimulationEngine` and the `Process`/`Recorder`
interfaces, tested against a throwaway dummy state. Now you build the real
state object every process in later stages will read and mutate.

## Goal

A single mutable `ReactorState` class that represents the complete reactor
at an instant in time, with species that are entirely configurable (no
hardcoded names anywhere in this file).

## Files to Create

- `core/state.py`

## Public API

```python
# core/state.py
from dataclasses import dataclass, field

@dataclass
class ReactorState:
    time: float = 0.0
    volume: float = 1.0
    liquid: dict[str, float] = field(default_factory=dict)
    vapor: dict[str, float] = field(default_factory=dict)
    inflows: dict[str, float] = field(default_factory=dict)   # last-step aggregated species inflow rates, for recording
    outflow_rate: float = 0.0                                  # last-step outlet volumetric flow rate
    derived: dict[str, float] = field(default_factory=dict)    # scratch space: reaction rates, measured values, etc.
    metadata: dict = field(default_factory=dict)               # static run info: species list, units, run id, ...

    # --- species accessors -------------------------------------------------
    def get(self, species: str, phase: str = "liquid") -> float: ...
    def set(self, species: str, value: float, phase: str = "liquid") -> None: ...
    def add(self, species: str, delta: float, phase: str = "liquid") -> None: ...
    def concentration(self, species: str, phase: str = "liquid") -> float:
        """quantity / volume. Vapor concentration uses the same `volume`
        field unless/until a separate vapor headspace volume is introduced
        (out of scope here — note it in a comment for a future stage)."""
        ...

    # --- bulk accessors ------------------------------------------------------
    def register_species(self, name: str, phase: str = "liquid", initial: float = 0.0) -> None:
        """Add a new species mid-run without touching any other code."""
        ...

    def total_mass(self, phase: str | None = None) -> float:
        """Sum of quantities in one phase, or both if phase is None."""
        ...

    def snapshot(self) -> dict:
        """Flatten the entire state into a single-level dict suitable for
        one tabular row, e.g. {"time":..., "volume":...,
        "liquid.A":..., "vapor.B":..., "derived.reaction_rate_1":...,
        ...}. This is what Stage 10's recorder will call every step."""
        ...

    def copy(self) -> "ReactorState":
        """Deep copy, for use in tests that need before/after comparison."""
        ...
```

## Behavioral Requirements

- Species are just dict keys. Nothing in this file may reference a species
  name like `"A"`, `"B"`, `"C"` except inside tests/examples.
- `phase` must be `"liquid"` or `"vapor"`; anything else raises
  `ValueError`.
- `get()` on an unregistered species should raise a clear `KeyError`-style
  error rather than silently returning `0.0` — silent zeros hide config
  mistakes (missing species in a reaction/stream definition). Provide
  `register_species` as the explicit, intentional way to add a species
  with a starting value.
- `add()` is the standard way processes should mutate quantities (as
  opposed to `set()`, which is for initialization/tests). Do **not** clamp
  negative values here — that's a per-process decision (some stages will
  choose to clamp, e.g. reactions/decay shouldn't let concentrations go
  negative; document this tension in a comment so later stages know where
  responsibility lies).
- `snapshot()` keys must be stable and predictable: `f"liquid.{name}"`,
  `f"vapor.{name}"`, `f"derived.{key}"`, plus top-level `time`, `volume`,
  `outflow_rate`. Do not include `metadata` in the snapshot (it's static,
  belongs in a separate run-level record — see Stage 10).
- `ReactorState` must not import anything from `signals/`, `processes/`,
  or `core/engine.py`. It is a pure data model.

## Out of Scope

- Anything about *how* species change over time (mixing/reactions/decay —
  Stages 5–7).
- Anything about vapor headspace volume being distinct from liquid volume
  — use the single `volume` field for now, leave a `# TODO` comment noting
  this simplification.

## Acceptance Criteria

`tests/core/test_state.py`:

1. Constructing a state with a few species via `register_species`, then
   `get`/`set`/`add` round-trip correctly for both phases.
2. `get()` on a never-registered species raises.
3. `concentration()` returns `quantity / volume` correctly, including when
   `volume` is not 1.0.
4. `total_mass()` with `phase=None` sums both liquid and vapor; with a
   phase argument sums only that phase.
5. `snapshot()` returns a flat dict with the exact expected keys for a
   state with 2 liquid species and 1 vapor species, plus `time`, `volume`,
   `outflow_rate` — and `metadata`/`inflows` behave as documented above
   (decide whether `inflows` appears in the snapshot and assert that
   choice consistently).
6. `copy()` produces an independent object — mutating the copy's `liquid`
   dict does not affect the original.
7. Invalid `phase` string raises `ValueError` from every accessor that
   takes a `phase` argument.

## Example

`examples/stage_02_demo.py`: build a `ReactorState` with species `A`
(liquid) and `B` (vapor), print `snapshot()`, mutate with `add`, print
again to show the change.
