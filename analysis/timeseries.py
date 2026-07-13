from __future__ import annotations

from pathlib import Path

import matplotlib.figure
import matplotlib.pyplot as plt
import pandas as pd


def load(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix == ".csv":
        return pd.read_csv(p)
    elif p.suffix == ".parquet":
        return pd.read_parquet(p)
    else:
        raise ValueError(f"Unsupported extension: {p.suffix!r}; use .csv or .parquet")


def plot_timeseries(
    df: pd.DataFrame,
    columns: list[str],
    time_column: str = "time",
) -> tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
    fig, ax = plt.subplots()
    for col in columns:
        ax.plot(df[time_column], df[col], label=col)
    ax.set_xlabel(time_column)
    ax.legend()
    return fig, ax


def moving_average(df: pd.DataFrame, column: str, window: int) -> pd.Series:
    return df[column].rolling(window=window, min_periods=1).mean()


def rolling_stats(df: pd.DataFrame, column: str, window: int) -> pd.DataFrame:
    roll = df[column].rolling(window=window, min_periods=1)
    return pd.DataFrame({
        "mean": roll.mean(),
        "std": roll.std(ddof=0),
        "min": roll.min(),
        "max": roll.max(),
    })


def lag_plot(
    df: pd.DataFrame,
    column: str,
    lag: int = 1,
) -> tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
    fig, ax = plt.subplots()
    ax.scatter(df[column].shift(lag), df[column])
    ax.set_xlabel(f"{column} (t-{lag})")
    ax.set_ylabel(f"{column} (t)")
    return fig, ax
