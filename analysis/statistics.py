from __future__ import annotations

import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def summary_statistics(
    df: pd.DataFrame,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    if columns is None:
        cols = df.select_dtypes(include="number").columns.tolist()
    else:
        cols = [c for c in columns if c in df and pd.api.types.is_numeric_dtype(df[c])]
    return df[cols].describe().loc[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]]


def correlation_matrix(
    df: pd.DataFrame,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    if columns is None:
        cols = df.select_dtypes(include="number").columns.tolist()
    else:
        cols = [c for c in columns if c in df and pd.api.types.is_numeric_dtype(df[c])]
    return df[cols].corr()


def autocorrelation(series: pd.Series, max_lag: int) -> pd.Series:
    result = {}
    for lag in range(max_lag + 1):
        result[lag] = series.autocorr(lag=lag) if lag > 0 else 1.0
    return pd.Series(result, name="autocorrelation")


def distribution(
    df: pd.DataFrame,
    column: str,
    bins: int = 30,
) -> tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
    fig, ax = plt.subplots()
    ax.hist(df[column].dropna(), bins=bins)
    ax.set_xlabel(column)
    ax.set_ylabel("Frequency")
    return fig, ax
