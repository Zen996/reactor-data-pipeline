from __future__ import annotations

import math

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")

from analysis.statistics import (
    autocorrelation,
    correlation_matrix,
    distribution,
    summary_statistics,
)


@pytest.fixture
def small_df() -> pd.DataFrame:
    return pd.DataFrame({
        "a": [1.0, 2.0, 3.0, 4.0, 5.0],
        "b": [10.0, 20.0, 30.0, 40.0, 50.0],
        "c": ["x", "y", "z", "w", "v"],
    })


class TestSummaryStatistics:
    def test_columns_present(self, small_df: pd.DataFrame) -> None:
        s = summary_statistics(small_df)
        assert "a" in s.columns
        assert "b" in s.columns
        assert "c" not in s.columns

    def test_known_values(self) -> None:
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
        s = summary_statistics(df)
        assert s.loc["count", "x"] == 3.0
        assert s.loc["mean", "x"] == 2.0
        assert s.loc["min", "x"] == 1.0
        assert s.loc["max", "x"] == 3.0

    def test_specific_columns(self, small_df: pd.DataFrame) -> None:
        s = summary_statistics(small_df, columns=["a"])
        assert "a" in s.columns
        assert "b" not in s.columns


class TestCorrelationMatrix:
    def test_perfect_correlation(self) -> None:
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0, 6.0]})
        cm = correlation_matrix(df)
        assert cm.loc["x", "y"] == pytest.approx(1.0, abs=1e-10)

    def test_non_numeric_ignored(self, small_df: pd.DataFrame) -> None:
        cm = correlation_matrix(small_df)
        assert "c" not in cm.columns
        assert "a" in cm.columns

    def test_diagonal_is_one(self) -> None:
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [5.0, 3.0, 1.0]})
        cm = correlation_matrix(df)
        assert cm.loc["x", "x"] == pytest.approx(1.0)
        assert cm.loc["y", "y"] == pytest.approx(1.0)


class TestAutocorrelation:
    def test_lag_zero_is_one(self) -> None:
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        ac = autocorrelation(s, max_lag=3)
        assert ac[0] == pytest.approx(1.0)

    def test_periodic_signal(self) -> None:
        t = np.linspace(0, 8 * math.pi, 400)
        s = pd.Series(np.sin(t))
        ac = autocorrelation(s, max_lag=150)
        assert ac[100] > 0.9

    def test_short_series(self) -> None:
        s = pd.Series([1.0, 2.0, 3.0, 4.0])
        ac = autocorrelation(s, max_lag=3)
        assert ac[0] == pytest.approx(1.0)
        assert ac[1] == pytest.approx(1.0)
        assert ac[2] == pytest.approx(1.0)
        assert pd.isna(ac[3])


class TestDistribution:
    def test_returns_figure(self, small_df: pd.DataFrame) -> None:
        fig, ax = distribution(small_df, "a", bins=5)
        assert fig is not None
        assert ax is not None
