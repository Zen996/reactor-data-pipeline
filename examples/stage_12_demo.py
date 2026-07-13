from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analysis.timeseries import (
    load,
    moving_average,
    plot_timeseries,
    rolling_stats,
)
from analysis.statistics import (
    autocorrelation,
    correlation_matrix,
    summary_statistics,
)
from config.builder import build_engine
from config.simulation import SimulationConfig

cfg = SimulationConfig.load(
    os.path.join(os.path.dirname(__file__), "configs", "disturbance_study.yaml")
)
cfg.recorder_output = None

engine = build_engine(cfg)
engine.run()
df = engine._config_recorder.to_dataframe()

out_dir = os.path.join(os.path.dirname(__file__), "stage_12_output")
os.makedirs(out_dir, exist_ok=True)

print("=== summary_statistics ===")
print(summary_statistics(df).to_string())
print()

print("=== correlation_matrix ===")
cm = correlation_matrix(df)
print(cm.to_string())
print()

fig, ax = plot_timeseries(df, columns=["liquid.A", "liquid.B", "derived.sensor_A"])
fig.savefig(os.path.join(out_dir, "timeseries.png"))
plt.close(fig)

stats = rolling_stats(df, "liquid.A", window=10)
fig2, ax2 = plt.subplots()
ax2.plot(df["time"], stats["mean"], label="MA")
ax2.plot(df["time"], stats["std"], label="Std")
ax2.legend()
fig2.savefig(os.path.join(out_dir, "rolling.png"))
plt.close(fig2)

ac = autocorrelation(df["liquid.A"], max_lag=50)
fig3, ax3 = plt.subplots()
ax3.plot(ac.index, ac.values)
ax3.set_xlabel("Lag")
ax3.set_ylabel("Autocorrelation")
fig3.savefig(os.path.join(out_dir, "autocorr.png"))
plt.close(fig3)

print(f"Plots saved to {out_dir}/")
