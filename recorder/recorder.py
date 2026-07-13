from __future__ import annotations

import json
from typing import Any

import pandas as pd

from core.process import Recorder as RecorderBase


class TabularRecorder(RecorderBase):
    def __init__(self, run_metadata: dict | None = None) -> None:
        self._run_metadata = run_metadata if run_metadata is not None else {}
        self._rows: list[dict[str, Any]] = []
        self._df: pd.DataFrame | None = None

    def record(self, state: Any, sim_time: float) -> None:
        row = state.snapshot()
        row["sim_time"] = sim_time
        self._rows.append(row)
        self._df = None

    def finalize(self) -> None:
        pass

    def to_dataframe(self) -> pd.DataFrame:
        if self._df is None:
            if not self._rows:
                self._df = pd.DataFrame()
            else:
                self._df = pd.DataFrame(self._rows).sort_values("sim_time").reset_index(drop=True)
        return self._df

    def truncate_after(self, time: float) -> None:
        """Drop every buffered row with sim_time > time."""
        self._rows = [r for r in self._rows if r.get("sim_time", 0.0) <= time]
        self._df = None

    def metadata(self) -> dict:
        return self._run_metadata

    def export_csv(self, path: str) -> None:
        self.to_dataframe().to_csv(path, index=False)

    def export_parquet(self, path: str) -> None:
        self.to_dataframe().to_parquet(path, engine="pyarrow", index=False)

    def export_metadata(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self._run_metadata, f, indent=2)
