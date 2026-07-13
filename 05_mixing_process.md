# Stage 5 — Mixing Process

## Context

You now have `ReactorState` (Stage 2) and `InputStream` (Stage 4). This is
the first real `Process` (Stage 1 interface) — it's what actually moves
material into and out of the tank each timestep, under a perfect-mixing
assumption (the reactor's bulk composition is uniform and equal to the
outlet composition).

## Files to Create

- `processes/mixing.py`

## Public API

```python
# processes/mixing.py
from core.process import Process
from core.stream import InputStream
from signals.base import Signal

class MixingProcess(Process):
    def __init__(
        self,
        streams: list[InputStream],
        outflow_rate: Signal | float | None = None,
    ) -> None:
        """
        outflow_rate: volumetric outlet flow rate, as a Signal, a fixed
            float, or None. If None, outflow_rate at each step is set
            equal to total inflow rate (constant-volume operation) —
            document this default clearly since it's a meaningful modeling
            choice, not an arbitrary default.
        """

    def execute(self, state, dt: float) -> None: ...
```

## Behavioral Requirements

1. For each active stream, compute `species_inflow(state.time)` and add
   `rate * dt` to the corresponding phase dict on `state` (via
   `state.add(...)`).
2. Sum all streams' `flow_rate(state.time)` → `total_in`.
3. Resolve `outflow_rate` for this step: constant, signal-evaluated at
   `state.time`, or `total_in` if unset.
4. Outlet removal is proportional to current bulk composition (perfect
   mixing): for each species present in `state.liquid` (mixing only
   affects the liquid phase's outlet — vapor outlet/venting is a
   manipulation concern, Stage 8), remove
   `outflow_rate * state.concentration(species) * dt`. Do this using the
   concentration *before* this step's inflow was added, or after? Pick a
   convention (documented choice: apply inflow first, then compute outlet
   removal from the updated bulk — this is the more common
   semi-implicit/Euler convention for CSTRs) and be consistent; write this
   down as a code comment since it affects mass-balance test tolerances.
5. Update `state.volume += (total_in - outflow_rate) * dt`. Guard against
   `state.volume` going to zero or negative (clamp to some small epsilon
   and consider it worth a warning, not a crash, since this is
   configuration-driven data and shouldn't hard-fail a whole simulation
   run over an edge case).
6. Record `state.inflows` (species → rate, aggregated across streams) and
   `state.outflow_rate` for this step, since Stage 10's recorder will want
   them.
7. Species referenced by a stream's composition that don't yet exist on
   `state` should be auto-registered (call `state.register_species`)
   rather than raising — a new disturbance feed introducing a trace
   species shouldn't require touching `ReactorState` setup code.

## Out of Scope

- Reactions, decay, equilibrium (Stages 6–7) — this process only mixes and
  removes proportionally; it does not transform species into each other.
- Vapor-phase venting (Stage 8's manipulation framework).

## Acceptance Criteria

`tests/processes/test_mixing.py`:

1. Single constant stream, no explicit `outflow_rate` (defaults to
   `total_in`) → after one step, `state.volume` is unchanged (within
   floating point tolerance) and species quantities increased by the
   correct inflow amount minus the correct outlet removal.
2. Mass-balance check over many steps with a constant stream and default
   outflow: total liquid mass converges to a stable value rather than
   diverging or going negative.
3. Two streams feeding different species simultaneously — verify both
   species' quantities update independently and correctly.
4. Explicit fixed `outflow_rate` different from `total_in` — verify
   `state.volume` increases or decreases as expected.
5. A stream introducing a brand-new species not previously registered on
   `state` — verify it gets auto-registered with the correct inflow
   applied, not a crash.
6. An inactive stream (Stage 4's `active=False`) contributes nothing.

## Example

`examples/stage_05_demo.py`: one `ReactorState` with species A and B, one
`InputStream` feeding A, run `MixingProcess` manually for 20 steps (no
engine needed yet, or use the Stage 1 engine with just this one process),
print species quantities and volume over time.
