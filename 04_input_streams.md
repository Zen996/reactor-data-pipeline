# Stage 4 — Input Streams

## Context

You have `Signal` objects (Stage 3) that produce time-varying scalars, and
a `ReactorState` (Stage 2) with liquid/vapor species. This stage bridges
them: an `InputStream` describes one physical feed line into the reactor,
with a flow rate and a composition, both driven by signals.

## Files to Create

- `core/stream.py`

*(This file has no home in the original architecture sketch — see the note
in `00_overview.md`. It lives in `core/` because both `config/` (Stage 11)
and `processes/mixing.py` (Stage 5) need it, and it's a data/behavior
abstraction, not a `Process`.)*

## Public API

```python
# core/stream.py
from signals.base import Signal

class InputStream:
    def __init__(
        self,
        name: str,
        flow_signal: Signal,
        composition: dict[str, Signal],
        phase: str = "liquid",
        active: bool = True,
    ) -> None:
        """
        flow_signal: value(t) -> volumetric flow rate of this stream.
        composition: species name -> Signal giving that species'
            *concentration* in the feed (same units as ReactorState
            concentrations), not a fraction. Concentrations don't need to
            sum to anything in particular — that's a modeling choice made
            per experiment, not enforced here.
        phase: which phase this stream feeds into ("liquid" or "vapor").
        """

    def flow_rate(self, t: float) -> float: ...

    def species_inflow(self, t: float) -> dict[str, float]:
        """species -> inflow *rate* (concentration * flow_rate), at time t.
        Does not integrate over dt — that's the mixing process's job."""

    def set_active(self, active: bool) -> None:
        """Allow a manipulation (Stage 8) to turn a stream on/off later
        without recreating it."""
```

## Behavioral Requirements

- `flow_rate(t)` returns `0.0` when `active is False`, regardless of what
  `flow_signal` would otherwise say — "inactive" must be a hard override,
  not just a modeling nuance, since Stage 8 manipulations will toggle this.
- `species_inflow(t)` similarly returns all-zero when inactive.
- `phase` validated same as `ReactorState` (`"liquid"` or `"vapor"`,
  else `ValueError`).
- Multiple `InputStream` instances are just held in a `list[InputStream]`
  by whatever uses them (Stage 5's `MixingProcess`) — this class itself
  has no notion of "the other streams."
- No coupling to `ReactorState` here — `InputStream` only knows about
  signals and time. Keep it a pure, independently testable unit.

## Out of Scope

- Actually applying inflow to a `ReactorState` (Stage 5).
- Deciding which streams exist for a given experiment (Stage 11).

## Acceptance Criteria

`tests/core/test_stream.py`:

1. With `Constant` flow and `Constant` composition for two species,
   `species_inflow(t)` returns `flow_rate * concentration` for each,
   matching hand-computed values.
2. With a `Step` flow signal, `flow_rate(t)` matches before/after the
   step time.
3. `active=False` (or after `set_active(False)`) makes both `flow_rate`
   and `species_inflow` return zero at any `t`, even though the underlying
   signals would return nonzero.
4. Invalid `phase` raises `ValueError`.
5. A composition dict with signals that vary independently over time
   (e.g. one `Constant`, one `Sinusoid`) produces per-species inflow rates
   that vary independently and correctly at several sample times.

## Example

`examples/stage_04_demo.py`: two streams — one constant "base feed" of
species A, one `Step`-flow "disturbance feed" of species B kicking in at
`t=50` — print `species_inflow(t)` for both across a short time range.
