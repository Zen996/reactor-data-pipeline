from __future__ import annotations

import json
import math
import os
import tempfile

import pandas as pd
import pytest

from core.engine import SimulationEngine
from core.process import Process
from core.state import ReactorState
from processes.mixing import MixingProcess
from processes.reaction import Reaction, ReactionProcess
from recorder.recorder import TabularRecorder
from signals.constant import Constant


class _RecorderOnlyProcess(Process):
    def __init__(self, recorder: TabularRecorder) -> None:
        self._recorder = recorder

    def execute(self, state: ReactorState, dt: float) -> None:
        pass


def test_tabular_recorder_shape() -> None:
    state = ReactorState()
    state.register_species("A", "liquid", 10.0)
    state.register_species("B", "vapor", 5.0)
    recorder = TabularRecorder({"dt": 0.1, "species": ["A", "B"]})
    proc = MixingProcess(streams=[], outflow_rate=Constant(1.0))
    engine = SimulationEngine(
        initial_state=state,
        processes=[proc],
        recorder=recorder,
        dt=0.1,
        duration=1.0,
    )
    engine.run()
    df = recorder.to_dataframe()
    assert df.shape[0] == 10
    for col in ["sim_time", "volume", "liquid.A", "vapor.B"]:
        assert col in df.columns


def test_export_csv_roundtrip() -> None:
    state = ReactorState()
    state.register_species("X", "liquid", 2.0)
    recorder = TabularRecorder()
    proc = _RecorderOnlyProcess(recorder)
    engine = SimulationEngine(
        initial_state=state,
        processes=[proc],
        recorder=recorder,
        dt=0.2,
        duration=1.0,
    )
    engine.run()

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "out.csv")
        recorder.export_csv(path)
        reread = pd.read_csv(path)
        original = recorder.to_dataframe()
        for col in original.columns:
            if original[col].dtype.kind == "f":
                assert reread[col].fillna(-999).values == pytest.approx(
                    original[col].fillna(-999).values, rel=1e-6
                )
            else:
                assert (reread[col] == original[col]).all()


def test_export_parquet_exact_roundtrip() -> None:
    state = ReactorState()
    state.register_species("Y", "liquid", 3.0)
    recorder = TabularRecorder()
    proc = _RecorderOnlyProcess(recorder)
    engine = SimulationEngine(
        initial_state=state,
        processes=[proc],
        recorder=recorder,
        dt=0.2,
        duration=1.0,
    )
    engine.run()

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "out.parquet")
        recorder.export_parquet(path)
        reread = pd.read_parquet(path)
        original = recorder.to_dataframe()
        pd.testing.assert_frame_equal(original, reread)


def test_export_metadata() -> None:
    meta = {"dt": 0.1, "seed": 42, "config": "demo"}
    recorder = TabularRecorder(run_metadata=meta)
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "meta.json")
        recorder.export_metadata(path)
        with open(path) as f:
            loaded = json.load(f)
    assert loaded == meta


def test_mid_run_species_auto_registration() -> None:
    state = ReactorState()
    state.register_species("A", "liquid", 5.0)
    recorder = TabularRecorder()
    step_count = 0

    class _LateSpeciesProcess(Process):
        def execute(self, st: ReactorState, dt: float) -> None:
            nonlocal step_count
            step_count += 1
            if step_count == 3:
                st.register_species("B", "liquid", 3.0)

    engine = SimulationEngine(
        initial_state=state,
        processes=[_LateSpeciesProcess()],
        recorder=recorder,
        dt=0.1,
        duration=1.0,
    )
    engine.run()
    df = recorder.to_dataframe()
    assert "liquid.A" in df.columns
    assert "liquid.B" in df.columns
    assert df["liquid.B"].isna().iloc[0:2].all()
    assert df["liquid.B"].iloc[2] == pytest.approx(3.0)
