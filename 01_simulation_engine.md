# Stage 1 — Simulation Engine

## Context

First stage — nothing exists yet. You are building the orchestration core
that every later stage plugs into. `ReactorState` (Stage 2) doesn't exist
yet, so this stage tests against a minimal stand-in state object.

## Goal

A fixed-timestep simulation loop that executes an ordered list of `Process`
objects each step and hands the resulting state to a recorder, with zero
knowledge of what any process or the recorder actually does.

## Files to Create

- `core/process.py`
- `core/engine.py`

## Public API

```python
# core/process.py
from abc import ABC, abstractmethod

class Process(ABC):
    """A single transformation applied to reactor state each timestep."""

    @abstractmethod
    def execute(self, state, dt: float) -> None:
        """Mutate `state` in place to reflect the passage of `dt` seconds."""
        ...


class Recorder(ABC):
    """Minimal recorder contract. Fully implemented in Stage 10."""

    @abstractmethod
    def record(self, state, sim_time: float) -> None: ...

    def finalize(self) -> None:
        """Optional hook called once after the run completes. No-op by default."""
        return None
```

```python
# core/engine.py
class SimulationEngine:
    def __init__(
        self,
        initial_state,
        processes: list[Process],
        recorder: Recorder,
        dt: float,
        duration: float,
    ) -> None: ...

    def run(self) -> None:
        """Advance the simulation from t=0 to t=duration in steps of dt."""
        ...

    @property
    def state(self):
        """The current (or final, after run()) reactor state."""
        ...

    @property
    def current_time(self) -> float: ...
```

## Behavioral Requirements

- The loop runs while `current_time < duration` (use a small epsilon or
  round the step count via `n_steps = round(duration / dt)` to avoid
  floating-point drift — prefer the latter and iterate `for i in
  range(n_steps)`, computing `t = i * dt`).
- Each step: execute every process **in list order**, passing the same
  `dt`, then call `recorder.record(state, t)`.
- **Time contract**: the engine is the sole owner of the simulation clock.
  If `state` exposes a settable time attribute (duck-typed — don't import
  `ReactorState` here, this stage predates it), the engine sets it before
  running processes for that step. Use `getattr`/`hasattr` or a tiny
  `Protocol` for this so `core/engine.py` has no import dependency on
  `core/state.py`. Something like:

  ```python
  class HasTime(Protocol):
      time: float
  ```

- `dt` and `duration` must be positive; raise `ValueError` otherwise.
- After `run()` completes, call `recorder.finalize()` exactly once.
- The engine must contain **no** process-specific logic — no `if
  isinstance(process, ...)` branching, no special-casing any process type.
- Constructor should accept an empty `processes` list (degenerate but
  valid — just advances time and records).

## Out of Scope

- Anything about what a "reactor" contains (Stage 2).
- Anything about what any specific process computes (Stages 5–9).
- Real recording/export (Stage 10) — a fake in-memory recorder is enough
  for this stage's tests.

## Acceptance Criteria

Write `tests/core/test_engine.py` covering:

1. A dummy `Process` that increments a counter on a dummy state object,
   run for `duration=10, dt=1` → counter reaches exactly 10.
2. A dummy `Recorder` that appends `(sim_time, state)` tuples — length of
   the recorded log equals the number of steps, and recorded times are
   `0, 1, 2, ..., 9` (not `1..10` — record happens *after* processes run
   for the current step, using the time at the start of that step... pick
   one convention, document it in the docstring, and make the test assert
   that convention explicitly).
3. Multiple processes execute in the order they were passed in — assert
   with a list of processes that each append their own name to a shared
   log on the state.
4. `dt <= 0` or `duration <= 0` raises `ValueError`.
5. `recorder.finalize()` is called exactly once, after the last step, not
   once per step (use a call counter).
6. An empty `processes` list runs without error and still calls
   `recorder.record` once per step.

## Example

Create `examples/stage_01_demo.py`: a bare-bones script with a fake state
(e.g. `types.SimpleNamespace(time=0.0, value=0.0)`), one `Process` that
adds `1.0 * dt` to `state.value` each step, a `Recorder` that prints
`(sim_time, state.value)`, run for 5 seconds at `dt=1`. This demonstrates
the engine works before any real domain logic exists.
