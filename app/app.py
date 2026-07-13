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

experiment = get_experiment()

if experiment is None:
    st.sidebar.header("Configuration")
    config = render_config_editor()
    if config is not None:
        from config.builder import build_experiment
        exp = build_experiment(config)
        set_experiment(exp)
        st.rerun()
else:
    st.sidebar.header("Experiment Active")

    if st.sidebar.button("Reset", key="sidebar_reset"):
        session_reset()
        st.rerun()

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
            "Rewind target time", value=0.0, min_value=0.0,
            key="rewind_target",
        )

    col1, col2 = st.columns([1, 2])
    with col1:
        render_run_controls(experiment, checkpoints)
        render_live_params(experiment)
    with col2:
        render_charts(experiment)
