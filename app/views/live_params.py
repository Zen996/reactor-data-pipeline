from __future__ import annotations

import streamlit as st

from signals.constant import Constant
from signals.noise import GaussianNoise, UniformNoise
from signals.ramp import Ramp
from signals.sinusoid import Sinusoid, SquareWave, TriangleWave
from signals.step import Step


def render(experiment) -> None:
    st.subheader("Live Parameters")
    st.caption("Edits take effect on the *next* step — no rebuild needed.")

    _render_streams(experiment)
    _render_reactions(experiment)
    _render_manipulations(experiment)


def _render_streams(experiment) -> None:
    for i, stream in enumerate(experiment.streams):
        with st.expander(f"Stream: {stream.name}", expanded=False):
            active = st.checkbox("Active", value=stream.active, key=f"live_stream_{i}_active")
            if active != stream.active:
                stream.set_active(active)

            st.markdown("**Flow rate signal**")
            sig = stream._flow_signal
            new_sig = _edit_signal(sig, f"live_stream_{i}_flow")
            if new_sig is not None:
                stream._flow_signal = new_sig

            st.markdown("**Composition signals**")
            for species, sig in list(stream._composition.items()):
                new_sig = _edit_signal(sig, f"live_stream_{i}_comp_{species}")
                if new_sig is not None:
                    stream._composition[species] = new_sig


def _render_reactions(experiment) -> None:
    for j, rxn in enumerate(experiment.reactions):
        with st.expander(f"Reaction {j}", expanded=False):
            new_k = st.number_input(
                "Rate constant", value=float(rxn.rate_constant),
                key=f"live_reaction_{j}_k",
            )
            if new_k != rxn.rate_constant:
                rxn.rate_constant = new_k


def _render_manipulations(experiment) -> None:
    for k, m in enumerate(experiment.manipulations):
        with st.expander(f"Manipulation {k} ({type(m.trigger).__name__})", expanded=False):
            st.write(f"One-shot: {m.one_shot}")
            st.write(f"Fired at: {m.fired_at}")


def _edit_signal(sig, prefix: str) -> object | None:
    cls_name = type(sig).__name__
    st.write(f"Type: {cls_name}")

    if isinstance(sig, Constant):
        v = st.number_input("Value", value=sig._value, key=f"{prefix}_value")
        if v != sig._value:
            return Constant(v)
    elif isinstance(sig, Step):
        bl = st.number_input("Baseline", value=sig._baseline, key=f"{prefix}_baseline")
        sv = st.number_input("Step value", value=sig._step_value, key=f"{prefix}_sv")
        stm = st.number_input("Step time", value=sig._step_time, key=f"{prefix}_stm")
        if bl != sig._baseline or sv != sig._step_value or stm != sig._step_time:
            return Step(bl, sv, stm)
    elif isinstance(sig, Ramp):
        sv = st.number_input("Start value", value=sig._start_value, key=f"{prefix}_sv")
        sl = st.number_input("Slope", value=sig._slope, key=f"{prefix}_sl")
        if sv != sig._start_value or sl != sig._slope:
            return Ramp(sv, sl)
    elif isinstance(sig, Sinusoid):
        a = st.number_input("Amplitude", value=sig._amplitude, key=f"{prefix}_amp")
        f = st.number_input("Frequency", value=sig._frequency, key=f"{prefix}_freq")
        o = st.number_input("Offset", value=sig._offset, key=f"{prefix}_off")
        if a != sig._amplitude or f != sig._frequency or o != sig._offset:
            return Sinusoid(a, f, offset=o)
    elif isinstance(sig, (SquareWave, TriangleWave)):
        a = st.number_input("Amplitude", value=sig._amplitude, key=f"{prefix}_amp")
        f = st.number_input("Frequency", value=sig._frequency, key=f"{prefix}_freq")
        o = st.number_input("Offset", value=sig._offset, key=f"{prefix}_off")
        if a != sig._amplitude or f != sig._frequency or o != sig._offset:
            return type(sig)(a, f, offset=o)
    elif isinstance(sig, (GaussianNoise, UniformNoise)):
        st.write("(Noise signal — not editable in live params)")

    return None
