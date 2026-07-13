from __future__ import annotations

import os
import tempfile

import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")

from analysis.timeseries import lag_plot, load, moving_average, plot_timeseries, rolling_stats


@pytest.fixture
def small_df() -> pd.DataFrame:
    return pd.DataFrame({"time": [0.0, 1.0, 2.0, 3.0, 4.0], "x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})


class TestMovingAverage:
    def test_window_2(self, small_df: pd.DataFrame) -> None:
        result = moving_average(small_df, "x", window=2)
        expected = [1.0, 1.5, 2.5, 3.5, 4.5]
        assert result.tolist() == expected

    def test_window_full(self, small_df: pd.DataFrame) -> None:
        result = moving_average(small_df, "x", window=5)
        assert result.tolist() == [1.0, 1.5, 2.0, 2.5, 3.0]


class TestRollingStats:
    def test_window_2(self, small_df: pd.DataFrame) -> None:
        stats = rolling_stats(small_df, "x", window=2)
        assert stats["mean"].tolist() == [1.0, 1.5, 2.5, 3.5, 4.5]
        assert stats["min"].tolist() == [1, 1, 2, 3, 4]
        assert stats["max"].tolist() == [1, 2, 3, 4, 5]

    def test_output_columns(self, small_df: pd.DataFrame) -> None:
        stats = rolling_stats(small_df, "x", window=2)
        assert list(stats.columns) == ["mean", "std", "min", "max"]


class TestLoad:
    def test_csv_roundtrip(self) -> None:
        df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.csv")
            df.to_csv(path, index=False)
            loaded = load(path)
            pd.testing.assert_frame_equal(df, loaded)

    def test_parquet_roundtrip(self) -> None:
        df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.parquet")
            df.to_parquet(path, engine="pyarrow", index=False)
            loaded = load(path)
            pd.testing.assert_frame_equal(df, loaded)

    def test_unsupported_extension_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "data.txt")
            with open(path, "w") as f:
                f.write("a,b\n1,2\n")
            with pytest.raises(ValueError, match="Unsupported extension"):
                load(path)


class TestPlotting:
    def test_plot_timeseries_returns_figure(self, small_df: pd.DataFrame) -> None:
        fig, ax = plot_timeseries(small_df, columns=["x", "y"])
        assert fig is not None
        assert len(ax.lines) == 2

    def test_lag_plot_returns_figure(self, small_df: pd.DataFrame) -> None:
        fig, ax = lag_plot(small_df, "x", lag=1)
        assert fig is not None
        assert len(ax.collections) == 1
