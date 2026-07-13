from __future__ import annotations

import streamlit as st

from app.checkpoints import CheckpointStore


def get_experiment():
    return st.session_state.get("experiment")


def set_experiment(experiment) -> None:
    st.session_state["experiment"] = experiment
    st.session_state["checkpoints"] = CheckpointStore()


def reset() -> None:
    st.session_state.pop("experiment", None)
    st.session_state.pop("checkpoints", None)
