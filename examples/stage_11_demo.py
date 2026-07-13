from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.builder import build_engine, run_and_export
from config.simulation import SimulationConfig

print("=== Loading simple_reaction.json ===")
cfg1 = SimulationConfig.load(
    os.path.join(os.path.dirname(__file__), "configs", "simple_reaction.json")
)
engine1 = build_engine(cfg1)
engine1.run()
df1 = engine1._config_recorder.to_dataframe()
print(f"  Shape: {df1.shape}")
print(df1.head().to_string())
print()

print("=== Loading disturbance_study.yaml ===")
cfg2 = SimulationConfig.load(
    os.path.join(os.path.dirname(__file__), "configs", "disturbance_study.yaml")
)
engine2 = build_engine(cfg2)
engine2.run()
df2 = engine2._config_recorder.to_dataframe()
print(f"  Shape: {df2.shape}")
print(df2.head().to_string())
print()

out_dir = os.path.join(os.path.dirname(__file__), "stage_11_output")
os.makedirs(out_dir, exist_ok=True)

cfg1.recorder_output = os.path.join(out_dir, "simple_reaction")
run_and_export(build_engine(cfg1))

cfg2.recorder_output = os.path.join(out_dir, "disturbance_study")
run_and_export(build_engine(cfg2))

print(f"Exported both experiments to {out_dir}/")
