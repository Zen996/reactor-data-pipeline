# CSTR Simulator — Build Guide (Overview & Index)

This is the master index for a 12-stage build plan. Each stage has its own
markdown file (`01_...md` through `12_...md`). Hand the agent one file at a
time, in order — each stage assumes every previous stage is already
implemented and tested.

## Core Philosophy

This is **not** a chemistry simulator. It is a configurable dynamic system
that produces realistic-looking multivariate process data. Every "process"
(mixing, reaction, decay, equilibrium, manipulation, sensor noise) is just a
function that transforms a shared mutable `ReactorState` object:

```
Input Signals → Reactor State → [Mixing → Reactions → Decay → Equilibrium
                                  → Manipulations → Sensor Noise] →
                Updated Reactor State → Recorder
```

Every process implements the same interface: `execute(state, dt)`. The
engine never knows what a process actually does — it only sequences calls.
This uniformity is the single most important design invariant in the
project. **No stage should compromise it.**

## Design Priorities (in order)

1. Simplicity over chemical accuracy
2. Configurability over hardcoded logic
3. Extensibility through small, composable modules
4. Deterministic runs, with opt-in reproducible stochasticity

## Target Architecture

```
cstr_simulator/
    config/
        species.py          # Stage 11
        reactions.py         # Stage 11
        simulation.py         # Stage 11
        builder.py           # Stage 11 (factory: config -> SimulationEngine)
    core/
        engine.py            # Stage 1
        process.py            # Stage 1
        state.py             # Stage 2
        stream.py            # Stage 4 (addition — see note below)
    signals/
        base.py               # Stage 3
        constant.py           # Stage 3
        step.py               # Stage 3
        ramp.py               # Stage 3
        sinusoid.py            # Stage 3
        composite.py           # Stage 3
        noise.py               # Stage 3, formalized in Stage 9
    processes/
        mixing.py             # Stage 5
        reaction.py            # Stage 6
        decay.py               # Stage 7
        equilibrium.py          # Stage 7
        manipulation.py        # Stage 8
        sensors.py             # Stage 9
    recorder/
        recorder.py            # Stage 10
    analysis/
        timeseries.py           # Stage 12
        statistics.py           # Stage 12
    app/
        app.py                 # Stage 13 (Streamlit GUI)
        session.py              # Stage 13
        views/                  # Stage 13
    examples/
        stage_XX_demo.py        # one runnable demo per stage
    tests/
        (mirrors the src tree; one test module per source module)
```

> **Note on `core/stream.py`:** the original architecture sketch didn't list a
> home for the `InputStream` abstraction. Stage 4 adds it under `core/`
> because streams are a core concept reused by config (Stage 11) and mixing
> (Stage 5), not a "process." This is the one deliberate addition to the
> tree — call it out in a comment when you create it.

## Conventions Every Stage Must Follow

- **Python**: 3.11+, full type hints on all public functions/classes.
- **Style**: dataclasses (or `attrs`) for plain data containers; ABCs
  (`abc.ABC` / `typing.Protocol`) for interfaces.
- **Dependencies**: `numpy`, `pandas`, `pyarrow` (Parquet export), `pytest`.
  Add `pyyaml` only when Stage 11 needs config file loading. Add
  `matplotlib` only when Stage 12 needs plotting. Don't pull in dependencies
  ahead of the stage that needs them.
- **No hardcoded chemistry, species names, or reactions anywhere** outside
  of `examples/`. If a stage's implementation only works for one imaginary
  species named "A", it's wrong.
- **Testing**: every stage ships with `pytest` tests under `tests/` mirroring
  the source path (e.g. `core/engine.py` → `tests/core/test_engine.py`).
  A stage is not "done" until its tests pass and previous stages' tests
  still pass.
- **Docstrings**: every public class/function gets a one-paragraph
  docstring explaining intent, not just types.
- **Determinism**: nothing may call `numpy.random` or `random` directly
  outside of an explicitly passed/seeded generator (this becomes strict
  from Stage 9 onward, but write Stage 3's noise signals with a local seed
  from the start so there's no rework later).

## Workflow for the Agent

For each stage file:

1. Read the **Context** section to recall what already exists.
2. Implement the **Files to Create/Modify** and **Public API** exactly as
   scoped — resist building future-stage functionality early ("Out of
   Scope" sections exist for this reason).
3. Write the tests in **Acceptance Criteria** (or equivalent tests that
   check the same behavior).
4. Run the full test suite (not just the new tests) to confirm no
   regressions.
5. Add or update the matching `examples/stage_XX_demo.py` so the stage's
   behavior is runnable and visible on its own.
6. Stop. Do not start the next stage's file until told to.

## Stage Index

| Stage | File | Delivers |
|---|---|---|
| 1 | `01_simulation_engine.md` | Fixed-timestep engine + `Process` interface |
| 2 | `02_reactor_state.md` | `ReactorState` model |
| 3 | `03_signal_system.md` | Composable signal generators |
| 4 | `04_input_streams.md` | `InputStream` abstraction |
| 5 | `05_mixing_process.md` | Perfect-mixing process |
| 6 | `06_chemical_reactions.md` | Generic stoichiometric reactions |
| 7 | `07_physical_processes.md` | Decay + liquid/vapor equilibrium |
| 8 | `08_manipulations.md` | Event-driven manual interventions |
| 9 | `09_randomness.md` | Seeded, reproducible stochasticity |
| 10 | `10_recorder.md` | Tabular data capture + CSV/Parquet export |
| 11 | `11_configuration.md` | Config-driven experiment assembly |
| 12 | `12_analysis_utilities.md` | Standalone analysis/plotting toolkit |
| 13 | `13_interactive_gui.md` | Streamlit GUI: config editor + pause/tweak/continue + live charts (optional extension, builds on 1–12) |

## Future Extensions (do not build now, just don't preclude them)

Temperature, pressure, catalysts, inhibitors, heat exchangers, PID
controllers, multiple/networked reactors, recycle streams, distillation
units, sensor failures, equipment faults, process optimization, RL
environments, digital-twin experiments. All of these should be addable as
new `Process` implementations without touching `core/engine.py`. If any
stage's design makes one of these harder to bolt on later, that's a signal
to reconsider the design now.
