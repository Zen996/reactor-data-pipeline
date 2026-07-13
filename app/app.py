from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from app.session import get_experiment, reset as session_reset, set_experiment
from app.views.charts import render as render_charts
from app.views.config_editor import render as render_config_editor
from app.views.live_params import render as render_live_params
from app.views.run_controls import render as render_run_controls

st.set_page_config(layout="wide")
st.title("CSTR Simulation GUI")


# ---------------------------------------------------------------------------
# Helpers for the restart / edit workflow
# ---------------------------------------------------------------------------

def _save_last_config(config) -> None:
    """Store a serialisable copy of the config dict for restart/edit."""
    import dataclasses
    from config.reactions import DecayConfig, EquilibriumConfig, ReactionConfig
    from config.species import SpeciesConfig

    def _as_dict(obj):
        if isinstance(obj, (SpeciesConfig, ReactionConfig, DecayConfig, EquilibriumConfig)):
            return dataclasses.asdict(obj)
        return obj

    cfg_dict = {
        "species": [_as_dict(s) for s in config.species],
        "streams": list(config.streams),
        "reactions": [_as_dict(r) for r in config.reactions],
        "decays": [_as_dict(d) for d in config.decays],
        "equilibria": [_as_dict(e) for e in config.equilibria],
        "sensors": list(config.sensors),
        "outflow_rate": config.outflow_rate,
        "dt": config.dt,
        "duration": config.duration,
        "seed": config.seed,
        "max_volume": config.max_volume,
        "min_volume": config.min_volume,
    }
    st.session_state["last_config"] = cfg_dict


def _do_restart() -> None:
    """Rebuild the experiment from the saved config without showing the editor."""
    last = st.session_state.get("last_config")
    if last is None:
        return
    from config.simulation import SimulationConfig
    from config.builder import build_experiment
    cfg = SimulationConfig.from_dict(last)
    exp = build_experiment(cfg)
    set_experiment(exp)
    _save_last_config(cfg)


def _do_edit(last_cfg: dict) -> None:
    """Clear the experiment and pre-fill session_state so the config editor
    shows the saved values, allowing the user to modify them."""
    from app.views.config_editor import prefill_session_state
    session_reset()
    prefill_session_state(last_cfg)
    st.rerun()


# ---------------------------------------------------------------------------
# Main app logic
# ---------------------------------------------------------------------------

experiment = get_experiment()

if experiment is None:
    st.sidebar.header("Configuration")
    config = render_config_editor()
    if config is not None:
        from config.builder import build_experiment
        experiment = build_experiment(config)
        set_experiment(experiment)
        _save_last_config(config)

if experiment is not None:
    st.sidebar.header("Experiment Active")

    col_restart, col_edit = st.sidebar.columns(2)
    with col_restart:
        if st.button("Restart", key="sidebar_restart", type="primary"):
            _do_restart()
    with col_edit:
        last_cfg = st.session_state.get("last_config")
        if last_cfg is not None and st.button("Edit Config", key="sidebar_edit"):
            _do_edit(last_cfg)

    if st.sidebar.button("Reset", key="sidebar_reset"):
        session_reset()

    df = experiment.recorder.to_dataframe()
    if not df.empty:
        tmp_csv = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        experiment.recorder.export_csv(tmp_csv.name)
        with open(tmp_csv.name, "rb") as fh_csv:
            st.sidebar.download_button(
                "Download CSV", data=fh_csv, file_name="run.csv",
                key="dl_csv_btn",
            )
        tmp_pq = tempfile.NamedTemporaryFile(suffix=".parquet", delete=False)
        experiment.recorder.export_parquet(tmp_pq.name)
        with open(tmp_pq.name, "rb") as fh_pq:
            st.sidebar.download_button(
                "Download Parquet", data=fh_pq, file_name="run.parquet",
                key="dl_pq_btn",
            )

    checkpoints = st.session_state.get("checkpoints")
    if checkpoints is not None:
        st.sidebar.number_input(
            "Rewind target time", value=0.0,
            key="rewind_target",
        )

    col1, col2 = st.columns([1, 2])
    with col1:
        render_run_controls(experiment, checkpoints)
        render_live_params(experiment)
    with col2:
        render_charts(experiment)
