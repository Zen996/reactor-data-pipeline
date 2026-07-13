from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.engine import SimulationEngine
from core.state import ReactorState
from processes.mixing import MixingProcess
from processes.reaction import Reaction, ReactionProcess
from processes.sensors import SensorNoiseProcess, SensorSpec
from recorder.recorder import TabularRecorder
from signals.constant import Constant
from signals.noise import GaussianNoise

state = ReactorState()
state.register_species("A", "liquid", 10.0)
state.register_species("B", "liquid", 0.0)
state.register_species("C", "liquid", 0.0)

mixing = MixingProcess(
    streams=[],
    outflow_rate=Constant(1.0),
)

reaction = ReactionProcess([
    Reaction(reactants={"A": 1}, products={"B": 1}, rate_constant=0.5),
])

sensors = SensorNoiseProcess([
    SensorSpec(species="A", phase="liquid", noise=GaussianNoise(std=0.1, seed=42), output_key="sensor_A"),
    SensorSpec(species="B", phase="liquid", noise=GaussianNoise(std=0.05, seed=7), output_key="sensor_B"),
])

recorder = TabularRecorder(run_metadata={
    "dt": 0.1,
    "duration": 10.0,
    "species": ["A", "B", "C"],
    "description": "CSTR demo — mixing + reaction + sensor noise",
})

engine = SimulationEngine(
    initial_state=state,
    processes=[mixing, reaction, sensors],
    recorder=recorder,
    dt=0.1,
    duration=10.0,
)

engine.run()

df = recorder.to_dataframe()

out_dir = os.path.join(os.path.dirname(__file__), "stage_10_output")
os.makedirs(out_dir, exist_ok=True)

recorder.export_csv(os.path.join(out_dir, "run.csv"))
recorder.export_parquet(os.path.join(out_dir, "run.parquet"))
recorder.export_metadata(os.path.join(out_dir, "run.json"))

print("=== head ===")
print(df.head().to_string())
print()
print("=== describe ===")
print(df.describe().to_string())
print()
print(f"Exported CSV, Parquet, and metadata to {out_dir}/")
