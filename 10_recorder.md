# Stage 10 — Recorder

## Context

Every process from Stages 5–9 now populates `ReactorState` (including
`derived` for reaction rates, sensor readings, etc.) each step. Stage 1's
engine already calls `recorder.record(state, sim_time)` every step and
`recorder.finalize()` once at the end — but that recorder has been a
throwaway test double until now. This stage builds the real one.

## Files to Create

- `recorder/recorder.py`

## Public API

```python
# recorder/recorder.py
import pandas as pd
from core.process import Recorder as RecorderBase  # the Stage 1 ABC

class TabularRecorder(RecorderBase):
    def __init__(self, run_metadata: dict | None = None) -> None:
        """run_metadata: static, run-level info — species list, dt,
        duration, seed, config name/hash, etc. Kept separate from the
        per-step time-series rows."""

    def record(self, state, sim_time: float) -> None:
        """Append one row using state.snapshot() (Stage 2), plus
        sim_time. Buffer rows in memory (list of dicts) rather than
        building a DataFrame every step — that's an unnecessary
        per-step cost at scale."""

    def finalize(self) -> None:
        """Called once by the engine after the run. Use this as the hook
        to build the final DataFrame (or just leave it a no-op and build
        lazily in to_dataframe() — agent's choice, but to_dataframe()
        must work correctly either way)."""

    def to_dataframe(self) -> pd.DataFrame:
        """All recorded rows as a single DataFrame, one row per timestep,
        columns matching state.snapshot() keys (plus sim_time)."""

    def metadata(self) -> dict:
        """The run_metadata dict, for callers that want to persist it
        alongside the time series."""

    def export_csv(self, path: str) -> None: ...

    def export_parquet(self, path: str) -> None: ...

    def export_metadata(self, path: str) -> None:
        """Write run_metadata as a JSON sidecar file next to the main
        export (e.g. `path` = "run.json" alongside "run.csv"/"run.parquet")."""
```

## Behavioral Requirements

- Row order in the DataFrame must match recording order (i.e., simulation
  time order) — don't rely on dict ordering tricks that could break; sort
  or verify explicitly if there's any doubt.
- `sim_time` and `state.time` might differ depending on the Stage 1
  time-recording convention chosen earlier — reuse that same convention
  here; don't introduce a second, inconsistent notion of "when did this
  row happen."
- Missing keys across steps (e.g. a species registered mid-run via
  Stage 5/7's auto-registration) must not crash `to_dataframe()` — pandas
  will naturally fill missing columns with `NaN` for earlier rows; decide
  whether that's acceptable (it is — document it) or whether you want to
  backfill zeros, and be consistent.
- `export_parquet` must use `pyarrow` as the backend (`df.to_parquet(path,
  engine="pyarrow")`), matching the project's stated dependency.
- The recorder module must not import anything from `processes/` — it
  only depends on `core.process.Recorder`, `core.state` (for typing,
  optional), and standard data libraries. It must work with *any* object
  that has a `.snapshot()` method, not specifically `ReactorState`, to
  keep it decoupled (duck typing is fine; don't hard-import `ReactorState`
  if you can avoid it, though importing purely for a type hint is
  acceptable).

## Out of Scope

- Any analysis/plotting on the recorded data (Stage 12) — this stage is
  capture and export only.
- Streaming/incremental export during a long run (e.g. writing to disk
  every N steps) — buffer fully in memory and export at the end; note
  this as a known limitation for very long runs if you want, but it's not
  required to solve now.

## Acceptance Criteria

`tests/recorder/test_recorder.py`:

1. Run a small simulation (reuse Stage 1's engine with a couple of Stage
   5–7 processes) with a `TabularRecorder`; verify
   `to_dataframe().shape[0]` equals the number of steps and columns
   include the expected `time`/`volume`/`liquid.*`/`vapor.*`/`derived.*`
   keys from `ReactorState.snapshot()`.
2. `export_csv` then re-reading the CSV with `pandas.read_csv` reproduces
   the same values (within floating-point round-trip tolerance).
3. `export_parquet` then re-reading with `pandas.read_parquet` reproduces
   the same values exactly (Parquet preserves floats exactly, unlike CSV
   text round-tripping — assert on this distinction).
4. `export_metadata` writes valid JSON containing the `run_metadata`
   passed at construction.
5. A run where a species gets auto-registered partway through (Stage 5 or
   7 behavior) still produces a valid DataFrame without raising, with
   `NaN`/zeros (per your documented choice) for the species' earlier rows.

## Example

`examples/stage_10_demo.py`: run a simulation combining mixing + reaction
+ sensor noise, export both CSV and Parquet plus a metadata JSON, print
`df.head()` and `df.describe()` to eyeball the shape of the generated
dataset.
