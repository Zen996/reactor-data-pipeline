# Stage 9 — Randomness

## Context

`signals/noise.py` (Stage 3) already has `GaussianNoise`/`UniformNoise`
with their own local seeds. Every other stochastic use case so far
(reaction rate variation, feed disturbances, actuator variation, sensor
readings) doesn't exist yet. This stage formalizes reproducible randomness
project-wide and adds sensor noise as a real process.

## Goal

One coherent seeding strategy so that **the entire run** — sensor noise,
feed disturbance signals, reaction coefficient variation, actuator
variation — is fully reproducible from a single top-level seed, regardless
of how many stochastic components exist or what order processes execute
in.

## Files to Create / Modify

- `core/random_manager.py` (new)
- `processes/sensors.py` (new)
- `signals/noise.py` (modify: accept an externally-provided generator
  instead of only a local seed)

## Public API

```python
# core/random_manager.py
import numpy as np

class RandomManager:
    def __init__(self, seed: int | None) -> None:
        """Owns a numpy SeedSequence derived from `seed` (or from OS
        entropy if None — but note that None makes the run
        non-reproducible, which should be an explicit, logged choice, not
        a silent default in any example/config)."""

    def spawn(self, name: str) -> np.random.Generator:
        """Return a new, independent Generator for a named consumer (e.g.
        "sensor.temperature", "feed.disturbance_1",
        "reaction.rate_variation_0"). Calling spawn() twice with the same
        name should return generators seeded identically *within the same
        RandomManager instance* only if that's an explicit, documented
        feature (e.g. for resetting a specific consumer) — default
        behavior should be that each spawn() call advances an internal
        sequence so repeated calls give different, still-reproducible
        streams. Pick one behavior and document/test it precisely."""
```

```python
# signals/noise.py (modified)
class GaussianNoise(Signal):
    def __init__(self, mean: float = 0.0, std: float = 1.0,
                 generator: "np.random.Generator | None" = None,
                 seed: int | None = None) -> None:
        """Prefer `generator` (from RandomManager.spawn) when provided;
        fall back to a locally-seeded generator built from `seed` for
        standalone use (keeps Stage 3's tests passing unmodified)."""
# same pattern for UniformNoise
```

```python
# processes/sensors.py
from dataclasses import dataclass
from core.process import Process
from signals.base import Signal

@dataclass
class SensorSpec:
    species: str
    phase: str
    noise: Signal   # typically a GaussianNoise/UniformNoise instance
    output_key: str  # where the noisy reading is stored in state.derived

class SensorNoiseProcess(Process):
    def __init__(self, sensors: list[SensorSpec]) -> None: ...
    def execute(self, state, dt: float) -> None:
        """For each sensor, compute true_value =
        state.get(species, phase); write
        state.derived[output_key] = true_value + sensor.noise.value(state.time)
        (additive noise model — multiplicative is a reasonable
        alternative; pick additive for simplicity per project philosophy,
        note the choice). Critically: this must NOT mutate
        state.liquid/state.vapor — sensor noise represents a measurement
        artifact, not a real physical change, and Stage 10's recorder
        should be able to show both the true and measured values in the
        same output row."""
```

## Behavioral Requirements

- Nothing outside `RandomManager` and the generators it spawns may call
  `numpy.random` global functions or unseeded `random.random()` anywhere
  in `signals/`, `processes/`, or `core/`. Grep for this before
  considering the stage done.
- Two full simulation runs built from identical config and the same
  top-level seed must produce byte-identical (or numerically identical to
  floating-point precision) recorded output, regardless of how many
  stochastic components are involved or in what order processes execute.
- Two runs with different seeds must diverge in their stochastic
  components while any deterministic components remain identical.
- `SensorNoiseProcess` must leave `state.liquid`/`state.vapor` completely
  unchanged — verify this explicitly in tests, not just informally.
- Feed disturbances and reaction-coefficient variation don't need new
  process code — they're achieved by constructing `InputStream`
  composition signals or `Reaction.rate_constant`-driving signals using
  `GaussianNoise`/`UniformNoise` wired to a `RandomManager`-spawned
  generator. If `Reaction.rate_constant` is currently a plain `float`
  (Stage 6), you may need to widen it to accept `float | Signal` evaluated
  at `state.time` — do this as a small, backward-compatible change and
  update Stage 6's tests only if the interface genuinely changes (existing
  float-only tests should keep passing).

## Out of Scope

- Correlated/multivariate noise (e.g. noise sources sharing an underlying
  random factor) — independent noise sources only, for now.
- Random *structural* events (e.g. randomly choosing which manipulation
  fires) — only continuous-valued randomness is in scope.

## Acceptance Criteria

`tests/core/test_random_manager.py`:

1. Same top-level seed → `spawn("x")` on two separate `RandomManager`
   instances yields generators that produce identical sequences of
   `.normal()`/`.uniform()` draws.
2. Different top-level seeds → diverging sequences.
3. Within one `RandomManager` instance, `spawn("a")` and `spawn("b")`
   produce different, independent sequences (not the same stream twice).

`tests/processes/test_sensors.py`:

1. `SensorNoiseProcess` output in `state.derived[output_key]` differs
   from the true value (when noise std > 0) but `state.liquid`/`vapor`
   values are bit-identical before and after `execute()`.
2. Same seed piped through `RandomManager` → identical sequence of
   `state.derived[output_key]` values across two full runs.

`tests/integration/test_reproducibility.py` (new, full-stack):

1. Build a small end-to-end simulation (mixing + reaction + sensor noise,
   using signals from Stage 3/4 and processes from Stages 5, 6, 9) with a
   fixed seed, run it twice independently, and assert the two exported
   datasets (or in-memory recorded rows) are identical.

## Example

`examples/stage_09_demo.py`: run the same small simulation twice with
`seed=42` and once more with `seed=7`, print a hash or a few sampled rows
from each to show seed 42 vs seed 42 match and seed 42 vs seed 7 differ.
