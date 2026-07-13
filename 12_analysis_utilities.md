# Stage 12 — Analysis Utilities

## Context

Stage 11 completed the simulator proper — any experiment can now be
defined by configuration and run to produce a tabular dataset (Stage 10's
`TabularRecorder` output, in memory or exported to CSV/Parquet). This
final stage builds a standalone toolkit for exploring that data. It must
not import anything from `core/`, `processes/`, `signals/`, or `config/` —
it operates purely on DataFrames (or paths to exported files), so it's
equally useful on data from a Python run, a loaded CSV, or a completely
different data source that happens to share the same shape.

## Files to Create

- `analysis/timeseries.py`
- `analysis/statistics.py`

## Public API

```python
# analysis/timeseries.py
import pandas as pd

def load(path: str) -> pd.DataFrame:
    """Load a CSV or Parquet export by extension."""

def plot_timeseries(df: pd.DataFrame, columns: list[str], time_column: str = "time"):
    """Line plot of one or more columns against time. Returns the
    matplotlib Figure/Axes rather than calling plt.show(), so callers
    (tests, notebooks, scripts) control display/saving."""

def moving_average(df: pd.DataFrame, column: str, window: int) -> pd.Series: ...

def rolling_stats(df: pd.DataFrame, column: str, window: int) -> pd.DataFrame:
    """DataFrame with rolling mean/std/min/max columns for `column`."""

def lag_plot(df: pd.DataFrame, column: str, lag: int = 1):
    """Scatter of column[t] vs column[t - lag]. Returns the Figure/Axes."""
```

```python
# analysis/statistics.py
import pandas as pd

def summary_statistics(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Per-column count/mean/std/min/25%/50%/75%/max — essentially a
    thin, explicit wrapper on df.describe(), scoped to numeric columns
    if `columns` is None."""

def correlation_matrix(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame: ...

def autocorrelation(series: pd.Series, max_lag: int) -> pd.Series:
    """Index 0..max_lag, values = autocorrelation at each lag.
    autocorrelation[0] must equal 1.0 (or extremely close, floating point)."""

def distribution(df: pd.DataFrame, column: str, bins: int = 30):
    """Histogram of `column`. Returns the Figure/Axes."""
```

## Behavioral Requirements

- No function in this module may import `core`, `processes`, `signals`,
  or `config` — this is the one hard architectural boundary for this
  stage; a `grep -r "from core" analysis/` (etc.) should return nothing.
- Every plotting function takes a DataFrame (or an already-loaded Series)
  and returns a matplotlib object rather than showing/saving a file
  itself — callers decide what to do with the figure.
- `load()` should raise a clear error for unsupported extensions rather
  than silently misparsing.
- `correlation_matrix` and `summary_statistics` should gracefully drop or
  clearly ignore non-numeric columns (e.g. any string metadata that
  might've leaked into the DataFrame) rather than raising.
- `autocorrelation` should be implemented with a plain, well-understood
  method (Pearson correlation between the series and its lagged self,
  computed with `pandas.Series.autocorr` or an explicit implementation) —
  don't reach for a heavier dependency (e.g. `statsmodels`) just for this;
  numpy/pandas alone are sufficient for the fidelity this project needs.

## Out of Scope

- Any simulation logic whatsoever — if you find yourself wanting to
  import `ReactorState` "just for typing," use a plain `pd.DataFrame`
  type hint instead. This module's entire value is that it works on data
  from anywhere.
- Advanced statistical modeling (ARIMA, spectral analysis, changepoint
  detection, etc.) — the brief calls for descriptive/exploratory tools
  only; note anything fancier as a natural future extension if asked.

## Acceptance Criteria

`tests/analysis/test_timeseries.py` and `test_statistics.py`, built
against a small synthetic DataFrame (not a real simulation run — keep this
stage's tests decoupled too):

1. `moving_average`/`rolling_stats` produce the expected values for a
   hand-computable synthetic series (e.g. `[1,2,3,4,5]` with `window=2`).
2. `correlation_matrix` on two perfectly correlated columns returns `1.0`
   off-diagonal (within floating point tolerance); on two independent
   random columns returns something clearly not ±1.
3. `autocorrelation(series, max_lag=5)[0] == 1.0`; for a known periodic
   synthetic series (e.g. a sampled sine wave), autocorrelation shows the
   expected peak near the signal's period.
4. `summary_statistics` output includes `mean`, `std`, `min`, `max` rows/
   columns (whichever orientation you choose — be consistent and
   document it) matching manually computed values on a small known
   dataset.
5. `load()` correctly reads back a small CSV and a small Parquet file
   with identical resulting DataFrames (modulo the float-precision caveat
   already noted in Stage 10).
6. `load()` on an unsupported extension (e.g. `.txt`) raises a clear
   error rather than crashing unhelpfully or silently returning garbage.
7. Plotting functions run without raising and return a non-`None` object
   with the expected number of lines/points (e.g. `len(ax.lines) ==
   len(columns)` for `plot_timeseries`).

## Example

`examples/stage_12_demo.py`: run a full experiment via Stage 11's
`build_engine` (or load one of the exported Parquet files from Stage 10's
example), then call `plot_timeseries`, `rolling_stats`, `correlation_matrix`,
and `autocorrelation` on it, saving the resulting figures to
`examples/output/` so the whole pipeline — config to plots — is
demonstrated end to end in one script.
