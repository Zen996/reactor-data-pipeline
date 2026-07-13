# Stage 3 — Signal System

## Context

`ReactorState` (Stage 2) and the engine (Stage 1) exist but nothing feeds
the reactor yet. This stage builds the time-varying value generators that
Stage 4's `InputStream` and later stages (noise, manipulations) will all
consume. Signals do not touch `ReactorState` — they are pure functions of
time, independently testable.

## Goal

A small family of composable `Signal` objects, each exposing
`value(t: float) -> float`, that can be chained into arbitrarily complex
input profiles without modifying any simulator code.

## Files to Create

- `signals/base.py`
- `signals/constant.py`
- `signals/step.py`
- `signals/ramp.py` (also covers "linear until maximum")
- `signals/sinusoid.py` (also covers rectified sinusoid, square wave, triangle wave — group periodic waveforms here rather than adding new files, to match the given architecture tree)
- `signals/composite.py`
- `signals/noise.py` (Gaussian + uniform; seeding is finalized in Stage 9 — for now, accept a `seed: int | None` constructor argument and create a local `numpy.random.Generator` from it)

## Public API

```python
# signals/base.py
from abc import ABC, abstractmethod

class Signal(ABC):
    @abstractmethod
    def value(self, t: float) -> float: ...
```

```python
# signals/constant.py
class Constant(Signal):
    def __init__(self, value: float) -> None: ...
```

```python
# signals/step.py
class Step(Signal):
    def __init__(self, baseline: float, step_value: float, step_time: float) -> None:
        """value(t) = baseline for t < step_time, else step_value."""
```

```python
# signals/ramp.py
class Ramp(Signal):
    def __init__(self, start_value: float, slope: float, start_time: float = 0.0,
                 max_value: float | None = None, min_value: float | None = None) -> None:
        """value(t) = start_value for t < start_time, else
        start_value + slope * (t - start_time), clamped to
        [min_value, max_value] when provided. `max_value` alone gives
        "linear until maximum"."""
```

```python
# signals/sinusoid.py
class Sinusoid(Signal):
    def __init__(self, amplitude: float, frequency: float, phase: float = 0.0,
                 offset: float = 0.0, rectified: bool = False) -> None:
        """rectified=True takes abs() of the sinusoid before adding offset."""

class SquareWave(Signal):
    def __init__(self, amplitude: float, frequency: float, duty_cycle: float = 0.5,
                 offset: float = 0.0) -> None: ...

class TriangleWave(Signal):
    def __init__(self, amplitude: float, frequency: float, offset: float = 0.0) -> None: ...
```

```python
# signals/composite.py
class CompositeSignal(Signal):
    def __init__(self, segments: list[tuple[float, float, Signal]]) -> None:
        """segments = [(start_time, end_time, signal), ...], sorted and
        non-overlapping. value(t) dispatches to whichever segment contains
        t. Each sub-signal receives the *global* t (not t relative to
        segment start) unless a `relative_time: bool` flag says otherwise
        — pick one behavior, document it clearly, and be consistent."""

    def value(self, t: float) -> float: ...
```

```python
# signals/noise.py
class GaussianNoise(Signal):
    def __init__(self, mean: float = 0.0, std: float = 1.0, seed: int | None = None) -> None: ...

class UniformNoise(Signal):
    def __init__(self, low: float = 0.0, high: float = 1.0, seed: int | None = None) -> None: ...
```

## Behavioral Requirements

- Every signal is stateless with respect to *simulation progress* except
  the noise signals, which necessarily hold RNG state. Calling
  `value(t)` twice with the same `t` on a deterministic signal must return
  the same result; noise signals will (correctly) not — document this
  explicitly.
- `CompositeSignal` segments must be validated at construction: no gaps or
  overlaps required unless you explicitly support a "no active segment"
  fallback (e.g., return `0.0` or raise — pick one and document it).
- Frequencies are in Hz (cycles per second of simulation time), matching
  whatever time units `dt`/`duration` use elsewhere in the project (the
  project doesn't enforce units — just be internally consistent and say so
  in a module docstring).
- `SquareWave`/`TriangleWave` can be implemented directly, or as thin
  wrappers that reuse `Sinusoid`'s phase math — agent's choice, but no
  duplicated waveform math across files.

## Out of Scope

- Anything about how a signal's value gets applied to a species or a
  stream (Stage 4).
- Centralized/global seed management across many noise instances (Stage
  9). For now, each `GaussianNoise`/`UniformNoise` just needs its own
  seed argument.

## Acceptance Criteria

`tests/signals/test_*.py`, one file per module:

1. `Constant`: `value(t)` is the same for several arbitrary `t`.
2. `Step`: value is `baseline` just before `step_time` and `step_value` at
   and after it.
3. `Ramp`: value before `start_time` is `start_value`; value increases
   linearly after; value saturates at `max_value`/`min_value` when set.
4. `Sinusoid`: check known values at `t=0` and at quarter-period; check
   `rectified=True` never returns a value below `offset`.
5. `SquareWave`/`TriangleWave`: check shape at a few sample points across
   one period (e.g., square wave is high for `duty_cycle` fraction of the
   period).
6. `CompositeSignal`: reproduce the exact example from the project brief
   — `Constant` for `[0,100)`, `Step` for `[100,250)`, `Sinusoid` for
   `[250,500)` — and assert `value(t)` dispatches to the right sub-signal
   at sample points in each range, including boundary points.
7. `GaussianNoise`/`UniformNoise`: same seed → identical sequence of
   `value(t)` calls across two separate instances; different seeds →
   different sequences; values fall within `[low, high]` for uniform.

## Example

`examples/stage_03_demo.py`: build the exact composite example from the
brief and print `value(t)` for `t` in `range(0, 500, 25)` to visually
confirm the transitions land where expected.
