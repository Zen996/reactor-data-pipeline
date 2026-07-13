from __future__ import annotations

import streamlit as st

from analysis.timeseries import plot_timeseries


def render(experiment) -> None:
    df = experiment.recorder.to_dataframe()
    if df.empty:
        st.info("No data recorded yet. Advance the simulation to see charts.")
        return

    input_cols = [c for c in df.columns if c.startswith("stream.") and c.endswith(".flow_rate")]
    if input_cols:
        st.subheader("Input Streams")
        fig, ax = plot_timeseries(df, input_cols)
        st.pyplot(fig)

    state_cols = [c for c in df.columns if c.startswith("liquid.") or c.startswith("vapor.")]
    outlet_cols = [c for c in df.columns if c.startswith("outlet.")]
    derived_cols = [c for c in df.columns if c.startswith("derived.") and not c.startswith("derived.stream.")]
    plot_cols = state_cols + outlet_cols + derived_cols

    if plot_cols:
        st.subheader("Reactor / Output")
        fig, ax = plot_timeseries(df, plot_cols)
        st.pyplot(fig)
