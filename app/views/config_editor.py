from __future__ import annotations

import streamlit as st

from config.simulation import SimulationConfig


def render() -> SimulationConfig | None:
    with st.sidebar.form("config_form"):
        st.subheader("Species")
        n_species = st.number_input("Number of species", min_value=0, max_value=10, value=1, key="n_species")
        species_list = []
        for i in range(int(n_species)):
            c1, c2, c3 = st.columns([2, 1, 1])
            name = c1.text_input(f"Name", value="A", key=f"species_{i}_name")
            phase = c2.selectbox(f"Phase", ["liquid", "vapor"], key=f"species_{i}_phase")
            qty = c3.number_input(f"Initial", value=10.0, key=f"species_{i}_qty")
            species_list.append({"name": name, "phase": phase, "initial_quantity": qty})

        st.subheader("Streams")
        n_streams = st.number_input("Number of streams", min_value=0, max_value=10, value=1, key="n_streams")
        stream_list = []
        for i in range(int(n_streams)):
            with st.expander(f"Stream {i}", expanded=True):
                sname = st.text_input(f"Name", value="feed", key=f"stream_{i}_name")
                sphase = st.selectbox(f"Phase", ["liquid", "vapor"], key=f"stream_{i}_phase")
                st.markdown("**Flow signal**")
                stype = st.selectbox(f"Type", ["constant", "step", "ramp", "sinusoid", "square", "triangle", "gaussian_noise", "uniform_noise"], key=f"stream_{i}_flow_type")
                flow_sig = _signal_params(stype, f"stream_{i}_flow")
                st.markdown("**Composition (species → signal)**")
                n_comp = st.number_input("Number of composition species", min_value=0, max_value=5, value=1, key=f"stream_{i}_n_comp")
                comp = {}
                for j in range(int(n_comp)):
                    sp = st.text_input(f"Species", value="A", key=f"stream_{i}_comp_{j}_sp")
                    ctype = st.selectbox(f"Signal type", ["constant", "step", "ramp", "sinusoid", "square", "triangle"], key=f"stream_{i}_comp_{j}_type")
                    comp[sp] = _signal_params(ctype, f"stream_{i}_comp_{j}")
                active = st.checkbox("Active", value=True, key=f"stream_{i}_active")
                stream_list.append({"name": sname, "phase": sphase, "flow_signal": flow_sig, "composition": comp, "active": active})

        st.subheader("Reactions")
        n_reactions = st.number_input("Number of reactions", min_value=0, max_value=10, value=0, key="n_reactions")
        reaction_list = []
        for i in range(int(n_reactions)):
            with st.expander(f"Reaction {i}"):
                reactants = st.text_input("Reactants (e.g. A:1,B:2)", key=f"reaction_{i}_reactants")
                products = st.text_input("Products (e.g. B:1,C:1)", key=f"reaction_{i}_products")
                rk = st.number_input("Rate constant", value=0.1, key=f"reaction_{i}_k")
                reaction_list.append({
                    "reactants": _parse_species_dict(reactants),
                    "products": _parse_species_dict(products),
                    "rate_constant": rk,
                })

        st.subheader("Simulation")
        dt = st.number_input("dt", value=0.5, min_value=0.001, key="sim_dt")
        duration = st.number_input("Duration", value=20.0, min_value=0.1, key="sim_duration")
        seed = st.number_input("Seed", value=42, min_value=0, key="sim_seed")
        volume = st.number_input("Volume", value=1.0, min_value=0.001, key="sim_volume")

        built = st.form_submit_button("Build Experiment", type="primary", key="build_experiment_btn")

    if built:
        from config.species import SpeciesConfig
        from config.reactions import ReactionConfig

        return SimulationConfig(
            species=[SpeciesConfig(**s) for s in species_list],
            streams=stream_list,
            reactions=[ReactionConfig(**r) for r in reaction_list],
            dt=dt,
            duration=duration,
            seed=seed,
            volume=volume,
        )
    return None


def _signal_params(stype: str, prefix: str) -> dict:
    if stype == "constant":
        return {"type": "constant", "value": st.number_input("Value", value=1.0, key=f"{prefix}_value")}
    elif stype == "step":
        return {
            "type": "step",
            "baseline": st.number_input("Baseline", value=0.0, key=f"{prefix}_baseline"),
            "step_value": st.number_input("Step value", value=1.0, key=f"{prefix}_step_value"),
            "step_time": st.number_input("Step time", value=5.0, key=f"{prefix}_step_time"),
        }
    elif stype == "ramp":
        return {
            "type": "ramp",
            "start_value": st.number_input("Start value", value=0.0, key=f"{prefix}_start_value"),
            "slope": st.number_input("Slope", value=0.1, key=f"{prefix}_slope"),
            "start_time": st.number_input("Start time", value=0.0, key=f"{prefix}_start_time"),
        }
    elif stype == "sinusoid":
        return {
            "type": "sinusoid",
            "amplitude": st.number_input("Amplitude", value=0.5, key=f"{prefix}_amp"),
            "frequency": st.number_input("Frequency", value=0.05, key=f"{prefix}_freq"),
            "offset": st.number_input("Offset", value=1.0, key=f"{prefix}_offset"),
        }
    elif stype in ("square", "triangle"):
        return {
            "type": stype,
            "amplitude": st.number_input("Amplitude", value=0.5, key=f"{prefix}_amp"),
            "frequency": st.number_input("Frequency", value=0.05, key=f"{prefix}_freq"),
            "offset": st.number_input("Offset", value=1.0, key=f"{prefix}_offset"),
        }
    elif stype in ("gaussian_noise", "uniform_noise"):
        return {
            "type": stype,
            "mean" if stype == "gaussian_noise" else "low": st.number_input("Mean" if stype == "gaussian_noise" else "Low", value=0.0, key=f"{prefix}_a"),
            "std" if stype == "gaussian_noise" else "high": st.number_input("Std" if stype == "gaussian_noise" else "High", value=0.1, key=f"{prefix}_b"),
        }
    return {"type": "constant", "value": 1.0}


def _parse_species_dict(text: str) -> dict[str, int]:
    result = {}
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            sp, val = part.split(":", 1)
            result[sp.strip()] = int(val.strip())
        else:
            result[part] = 1
    return result
