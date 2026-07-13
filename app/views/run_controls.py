from __future__ import annotations

import streamlit as st

from app.checkpoints import CheckpointStore


def render(experiment, checkpoints: CheckpointStore) -> None:
    engine = experiment.engine
    config = experiment.config

    st.subheader("Run Controls")
    c1, c2 = st.columns([3, 1])

    max_target = min(engine._duration, engine._duration)
    current = engine.current_time
    with c1:
        target = st.number_input(
            "Run to time",
            min_value=current,
            max_value=max_target,
            value=min(current + 5.0, max_target),
            key="run_target",
        )
    with c2:
        st.metric("Current time", f"{current:.2f}")

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        if st.button("▶ Step once", key="step_once"):
            _advance_one(experiment, checkpoints)
    with col_b:
        if st.button("▶▶ Advance", key="advance"):
            _advance_to(experiment, checkpoints, target)
    with col_c:
        st.button("⏮ Rewind", key="rewind_btn", on_click=_do_rewind, args=(experiment, checkpoints))
    with col_d:
        if st.button("Reset", key="reset_btn"):
            from app.session import reset as session_reset
            session_reset()

    _has_stochastic = _check_stochastic(experiment)
    if _has_stochastic:
        st.caption(
            ":warning: Randomness is enabled — continuing from a rewind "
            "will not reproduce the original run past this point."
        )


def _advance_one(experiment, checkpoints) -> None:
    engine = experiment.engine
    engine.step()
    checkpoints.add(engine.current_time, engine.state)
    if engine.current_time >= engine._duration:
        engine._recorder.finalize()


def _advance_to(experiment, checkpoints, target: float) -> None:
    engine = experiment.engine
    while engine.current_time < target and engine.current_time < engine._duration:
        engine.step()
        checkpoints.add(engine.state.time, engine.state)
    engine._recorder.finalize()


def _do_rewind(experiment, checkpoints) -> None:
    target = st.session_state.get("rewind_target", 0.0)
    engine = experiment.engine
    if target < 0:
        st.warning("Rewind target must be >= 0.")
        return
    cp = checkpoints.nearest_at_or_before(target)
    if cp is None:
        st.warning("No checkpoint available at or before that time.")
        return
    landed_time = cp.time
    engine.restore(cp.state.copy(), landed_time)
    experiment.recorder.truncate_after(landed_time)
    checkpoints.drop_after(landed_time)
    for m in experiment.manipulations:
        if m.fired_at is not None and m.fired_at > landed_time:
            m.fired_at = None


def _check_stochastic(experiment) -> bool:
    for s in experiment.streams:
        if s is None:
            continue
        from signals.noise import GaussianNoise, UniformNoise
        if isinstance(s._flow_signal, (GaussianNoise, UniformNoise)):
            return True
        for sig in s._composition.values():
            if isinstance(sig, (GaussianNoise, UniformNoise)):
                return True
    return False
