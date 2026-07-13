# Stage 11 — Configuration

## Context

Every building block exists as of Stage 10: state, signals, streams,
mixing, reactions, decay, equilibrium, manipulations, randomness, and
recording. Right now, assembling an experiment means writing Python that
constructs all of these objects by hand (as the `examples/stage_XX_demo.py`
scripts do). This stage makes that assembly entirely data-driven, so a new
experiment requires only new configuration, never new code.

## Files to Create

- `config/species.py`
- `config/reactions.py`
- `config/simulation.py`
- `config/builder.py`

## Public API

```python
# config/species.py
from dataclasses import dataclass

@dataclass
class SpeciesConfig:
    name: str
    phase: str
    initial_quantity: float = 0.0
```

```python
# config/reactions.py
from dataclasses import dataclass

@dataclass
class ReactionConfig:
    reactants: dict[str, int]
    products: dict[str, int]
    rate_constant: float | dict   # dict form lets rate_constant be a signal spec (see below)
    order: dict[str, float] | None = None
    phase: str = "liquid"

@dataclass
class DecayConfig:
    species: str
    rate_constant: float | dict
    phase: str = "liquid"
    products: dict[str, int] | None = None

@dataclass
class EquilibriumConfig:
    species: str
    evaporation_coeff: float
    condensation_coeff: float
```

```python
# config/simulation.py
from dataclasses import dataclass, field

@dataclass
class StreamConfig:
    name: str
    phase: str
    flow_signal: dict          # signal spec, e.g. {"type": "constant", "value": 5.0}
    composition: dict[str, dict]  # species -> signal spec
    active: bool = True

@dataclass
class SimulationConfig:
    species: list       # list[SpeciesConfig]
    streams: list        # list[StreamConfig]
    reactions: list = field(default_factory=list)      # list[ReactionConfig]
    decays: list = field(default_factory=list)          # list[DecayConfig]
    equilibria: list = field(default_factory=list)      # list[EquilibriumConfig]
    manipulations: list = field(default_factory=list)   # raw dict specs, resolved in builder.py
    dt: float = 1.0
    duration: float = 100.0
    seed: int | None = None
    volume: float = 1.0
    recorder_output: str | None = None    # base path for exports, e.g. "runs/experiment1"

    @staticmethod
    def from_dict(d: dict) -> "SimulationConfig": ...

    @staticmethod
    def load(path: str) -> "SimulationConfig":
        """Load from a JSON or YAML file, chosen by file extension."""
```

```python
# config/builder.py
from core.engine import SimulationEngine

SIGNAL_REGISTRY: dict[str, type] = {
    "constant": ...,   # signals.constant.Constant
    "step": ...,
    "ramp": ...,
    "sinusoid": ...,
    "square": ...,
    "triangle": ...,
    "gaussian_noise": ...,
    "uniform_noise": ...,
    "composite": ...,  # recursive: segments reference nested signal specs
}

def build_signal(spec: dict, random_manager) -> "Signal":
    """Resolve a signal spec dict into a Signal instance via
    SIGNAL_REGISTRY. Noise signal specs receive a RandomManager-spawned
    generator (Stage 9), named by a stable path derived from where the
    spec sits in the config (e.g. "stream.disturbance_1.composition.A")
    so re-running the same config with the same seed is reproducible."""

def build_engine(config: "SimulationConfig") -> SimulationEngine:
    """The single entry point: given a fully-specified SimulationConfig,
    construct ReactorState, RandomManager, all InputStreams, all
    Processes (MixingProcess, ReactionProcess, DecayProcess,
    EquilibriumProcess, ManipulationProcess, SensorNoiseProcess if
    configured), the TabularRecorder, and return a ready-to-run
    SimulationEngine. This function is where every prior stage's pieces
    get wired together — it should contain assembly logic only, no new
    simulation behavior."""
```

## Behavioral Requirements

- `SIGNAL_REGISTRY` is the only place that maps a config `"type"` string
  to a class — adding a new signal type anywhere in the codebase should
  require touching only this registry, not `build_signal`'s control flow.
- `build_engine` must not hardcode any species names, reaction
  definitions, or stream setups — everything flows from `config`.
- Manipulation specs (triggers/actions) need a small registry of their own
  (mirroring `SIGNAL_REGISTRY`) since Stage 8 has multiple trigger and
  action types — e.g. `{"trigger": {"type": "time", "time": 200},
  "action": {"type": "vent_vapor", "species": null, "fraction": 0.3},
  "one_shot": true}`.
- `SimulationConfig.load` supports both JSON and YAML transparently by
  extension (`.json` vs `.yml`/`.yaml`); add `pyyaml` as a dependency only
  now, per the project's "don't pull in dependencies early" convention.
- Running two different experiments should be possible by writing two
  separate config files/objects and calling `build_engine` on each —
  zero source changes.
- Keep `build_engine` composeable with `RandomManager` from Stage 9:
  construct one `RandomManager(config.seed)` and pass it through to every
  place that needs a generator (noise signals, any stochastic
  rate-constant signals).

## Out of Scope

- A GUI or CLI for editing configs — plain Python dicts/dataclasses and
  JSON/YAML files are sufficient.
- Config validation beyond basic type/shape checks — deep semantic
  validation (e.g. "this reaction references a species not in
  `config.species`") is a nice-to-have; add a lightweight check if easy,
  but don't over-invest here.

## Acceptance Criteria

`tests/config/test_builder.py`:

1. A hand-written `SimulationConfig` (species, one stream, one reaction)
   built via `build_engine`, run for a short duration, produces a
   `TabularRecorder` DataFrame with the expected columns and row count —
   this is effectively an end-to-end smoke test exercising Stages 1–10
   entirely through config.
2. Two different `SimulationConfig` objects (different species/reactions)
   both build and run successfully without any code changes between them
   — this is the core acceptance test for "the simulator should run
   entirely from configuration."
3. `SimulationConfig.load` round-trips correctly for both a `.json` and a
   `.yaml` version of the same experiment (write both, load both, assert
   equal resulting configs or equal simulation outputs).
4. A config using `"gaussian_noise"` for a stream's composition, built and
   run twice with the same `seed`, produces identical output (reuses
   Stage 9's reproducibility guarantee end-to-end through the builder).
5. `CompositeSignal` specs with nested signal specs resolve correctly
   through `build_signal`'s recursion.

## Example

`examples/stage_11_demo.py` plus two example config files under
`examples/configs/` (e.g. `simple_reaction.json` and
`disturbance_study.yaml`) — load each, build, run, export, to demonstrate
the "new experiment = new config file" promise concretely.
