from __future__ import annotations

import streamlit as st

from analysis.timeseries import plot_timeseries


def render(experiment) -> None:
    df = experiment.recorder.to_dataframe()
    if df.empty:
        st.info("No data recorded yet. Advance the simulation to see charts.")
        return

    # snapshot stores stream columns as derived.stream.<name>.flow_rate
    input_cols = [c for c in df.columns if c.startswith("derived.stream.") and c.endswith(".flow_rate")]
    if input_cols:
        st.subheader("Input Streams")
        # column format: derived.stream.<stream_name>.flow_rate
        stream_names = sorted(set(c.split(".")[2] for c in input_cols))
        selected = []
        for sname in stream_names:
            col_key = f"chart_show_stream_{sname}"
            if col_key not in st.session_state:
                st.session_state[col_key] = True
            if st.checkbox(sname, value=True, key=col_key):
                selected.append(sname)
        if selected:
            cols_to_plot = [f"derived.stream.{s}.flow_rate" for s in selected]
            fig, ax = plot_timeseries(df, cols_to_plot)
            st.pyplot(fig)
        else:
            st.caption("(no streams selected)")

    # snapshot stores outlet columns as derived.outlet.<species>
    state_cols = [c for c in df.columns if c.startswith("liquid.") or c.startswith("vapor.")]
    outlet_cols = [c for c in df.columns if c.startswith("derived.outlet.")]
    derived_cols = [c for c in df.columns if c.startswith("derived.") and not c.startswith("derived.stream.") and not c.startswith("derived.outlet.")]
    all_reactor_cols = state_cols + outlet_cols + derived_cols

    if all_reactor_cols:
        st.subheader("Reactor / Output")
        selected = st.multiselect(
            "Columns to show",
            options=all_reactor_cols,
            default=list(all_reactor_cols),
            key="reactor_col_multiselect",
        )
        if selected:
            fig, ax = plot_timeseries(df, selected)
            st.pyplot(fig)
        else:
            st.caption("(no columns selected)")
