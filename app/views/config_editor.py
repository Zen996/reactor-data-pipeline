from __future__ import annotations

import streamlit as st

from config.simulation import SimulationConfig


def render() -> SimulationConfig | None:
    with st.sidebar:
        st.subheader("Species")
        n_species = st.number_input(
            "Number of species", min_value=0, max_value=10, value=1, key="n_species"
        )
        species_list = []
        for i in range(int(n_species)):
            c1, c2, c3 = st.columns([2, 1, 1])
            name = c1.text_input("Name", value="A", key=f"species_{i}_name")
            phase = c2.selectbox(
                "Phase", ["liquid", "vapor"], key=f"species_{i}_phase"
            )
            qty = c3.number_input("Initial (0 = stream-fed)", value=0.0, key=f"species_{i}_qty")
            species_list.append(
                {"name": name, "phase": phase, "initial_quantity": qty}
            )

        st.subheader("Streams")
        n_streams = st.number_input(
            "Number of streams", min_value=0, max_value=10, value=1, key="n_streams"
        )
        stream_list = []
        for i in range(int(n_streams)):
            with st.expander(f"Stream {i}", expanded=True):
                sname = st.text_input("Name", value="feed", key=f"stream_{i}_name")
                sphase = st.selectbox(
                    "Phase", ["liquid", "vapor"], key=f"stream_{i}_phase"
                )
                st.markdown("**Flow signal**")
                stype = st.selectbox(
                    "Type",
                    ["constant", "step", "ramp", "sinusoid", "square", "triangle",
                     "gaussian_noise", "uniform_noise"],
                    key=f"stream_{i}_flow_type",
                )
                flow_sig = _signal_params(stype, f"stream_{i}_flow")
                st.markdown("**Composition (species -> signal)**")
                n_comp = st.number_input(
                    "Number of composition species", min_value=0, max_value=5,
                    value=1, key=f"stream_{i}_n_comp",
                )
                comp = {}
                for j in range(int(n_comp)):
                    sp = st.text_input(
                        "Species", value="A", key=f"stream_{i}_comp_{j}_sp"
                    )
                    ctype = st.selectbox(
                        "Signal type",
                        ["constant", "step", "ramp", "sinusoid", "square", "triangle"],
                        key=f"stream_{i}_comp_{j}_type",
                    )
                    comp[sp] = _signal_params(ctype, f"stream_{i}_comp_{j}")
                active = st.checkbox("Active", value=True, key=f"stream_{i}_active")
                stream_list.append({
                    "name": sname,
                    "phase": sphase,
                    "flow_signal": flow_sig,
                    "composition": comp,
                    "active": active,
                })

        st.subheader("Reactions")
        n_reactions = st.number_input(
            "Number of reactions", min_value=0, max_value=10, value=0,
            key="n_reactions"
        )
        reaction_list = []
        for i in range(int(n_reactions)):
            with st.expander(f"Reaction {i}"):
                reactants = st.text_input(
                    "Reactants (e.g. A:1,B:2)", key=f"reaction_{i}_reactants"
                )
                products = st.text_input(
                    "Products (e.g. B:1,C:1)", key=f"reaction_{i}_products"
                )
                rk = st.number_input(
                    "Rate constant", value=0.1, key=f"reaction_{i}_k"
                )
                reaction_list.append({
                    "reactants": _parse_species_dict(reactants),
                    "products": _parse_species_dict(products),
                    "rate_constant": rk,
                })

        st.subheader("Decays")
        n_decays = st.number_input(
            "Number of decays", min_value=0, max_value=10, value=0,
            key="n_decays"
        )
        decay_list = []
        for i in range(int(n_decays)):
            with st.expander(f"Decay {i}"):
                dsp = st.text_input("Species", value="A", key=f"decay_{i}_species")
                dk = st.number_input("Rate constant", value=0.1, key=f"decay_{i}_k")
                dphase = st.selectbox(
                    "Phase", ["liquid", "vapor"], key=f"decay_{i}_phase"
                )
                dprod = st.text_input(
                    "Products (optional, e.g. B:1)", key=f"decay_{i}_products"
                )
                decay_list.append({
                    "species": dsp,
                    "rate_constant": dk,
                    "phase": dphase,
                    "products": _parse_species_dict_optional(dprod),
                })

        st.subheader("Equilibria")
        n_equilibria = st.number_input(
            "Number of equilibria", min_value=0, max_value=10, value=0,
            key="n_equilibria"
        )
        equilibrium_list = []
        for i in range(int(n_equilibria)):
            with st.expander(f"Equilibrium {i}"):
                esp = st.text_input("Species", value="A", key=f"equilibrium_{i}_species")
                evap = st.number_input(
                    "Evaporation coefficient", value=0.1, key=f"equilibrium_{i}_evap"
                )
                cond = st.number_input(
                    "Condensation coefficient", value=0.1, key=f"equilibrium_{i}_cond"
                )
                equilibrium_list.append({
                    "species": esp,
                    "evaporation_coeff": evap,
                    "condensation_coeff": cond,
                })

        st.subheader("Sensors")
        n_sensors = st.number_input(
            "Number of sensors", min_value=0, max_value=10, value=0,
            key="n_sensors"
        )
        sensor_list = []
        for i in range(int(n_sensors)):
            with st.expander(f"Sensor {i}"):
                ssp = st.text_input("Species", value="A", key=f"sensor_{i}_species")
                sph = st.selectbox(
                    "Phase", ["liquid", "vapor"], key=f"sensor_{i}_phase"
                )
                sn_type = st.selectbox(
                    "Noise type",
                    ["gaussian_noise", "uniform_noise"],
                    key=f"sensor_{i}_noise_type",
                )
                sn_params = {}
                if sn_type == "gaussian_noise":
                    sn_params = {
                        "type": "gaussian_noise",
                        "mean": st.number_input("Mean", value=0.0, key=f"sensor_{i}_noise_mean"),
                        "std": st.number_input("Std", value=0.1, key=f"sensor_{i}_noise_std"),
                    }
                else:
                    sn_params = {
                        "type": "uniform_noise",
                        "low": st.number_input("Low", value=-0.1, key=f"sensor_{i}_noise_low"),
                        "high": st.number_input("High", value=0.1, key=f"sensor_{i}_noise_high"),
                    }
                out_key = st.text_input(
                    "Output key", value=f"sensor_{i}", key=f"sensor_{i}_key"
                )
                sensor_list.append({
                    "species": ssp,
                    "phase": sph,
                    "noise": sn_params,
                    "output_key": out_key,
                })

        st.subheader("Reactor")
        outflow_mode = st.selectbox(
            "Outflow mode",
            ["constant_volume", "fixed", "signal"],
            key="outflow_mode",
        )
        outflow_rate = None
        if outflow_mode == "fixed":
            outflow_rate = st.number_input(
                "Outflow rate", value=1.0, min_value=0.0, key="outflow_rate_fixed"
            )
        elif outflow_mode == "signal":
            sig_type = st.selectbox(
                "Signal type",
                ["constant", "step", "ramp", "sinusoid", "square", "triangle"],
                key="outflow_signal_type",
            )
            outflow_rate = _signal_params(sig_type, "outflow_signal")

        st.subheader("Simulation")
        dt = st.number_input("dt", value=0.5, min_value=0.001, key="sim_dt")
        duration = st.number_input(
            "Duration", value=20.0, min_value=0.1, key="sim_duration"
        )
        seed = st.number_input("Seed", value=42, min_value=0, key="sim_seed")
        volume = st.number_input(
            "Volume", value=1.0, min_value=0.001, key="sim_volume"
        )

        _validate_names(species_list, stream_list)

        if st.button("Build Experiment", type="primary", key="build_experiment_btn"):
            from config.species import SpeciesConfig
            from config.reactions import DecayConfig, EquilibriumConfig, ReactionConfig

            return SimulationConfig(
                species=[SpeciesConfig(**s) for s in species_list],
                streams=stream_list,
                reactions=[ReactionConfig(**r) for r in reaction_list],
                decays=[DecayConfig(**d) for d in decay_list],
                equilibria=[EquilibriumConfig(**e) for e in equilibrium_list],
                sensors=sensor_list,
                outflow_rate=outflow_rate,
                dt=dt,
                duration=duration,
                seed=seed,
                volume=volume,
            )
    return None


def _signal_params(stype: str, prefix: str) -> dict:
    if stype == "constant":
        return {
            "type": "constant",
            "value": st.number_input("Value", value=1.0, key=f"{prefix}_value"),
        }
    elif stype == "step":
        return {
            "type": "step",
            "baseline": st.number_input("Baseline", value=0.0, key=f"{prefix}_baseline"),
            "step_value": st.number_input("Step value", value=1.0, key=f"{prefix}_step_value"),
            "step_time": st.number_input("Step time", value=5.0, key=f"{prefix}_step_time"),
        }
    elif stype == "ramp":
        c1, c2 = st.columns(2)
        max_val = c1.number_input("Max value", value=0.0, key=f"{prefix}_max_value")
        min_val = c2.number_input("Min value", value=0.0, key=f"{prefix}_min_value")
        return {
            "type": "ramp",
            "start_value": st.number_input("Start value", value=0.0, key=f"{prefix}_start_value"),
            "slope": st.number_input("Slope", value=0.1, key=f"{prefix}_slope"),
            "start_time": st.number_input("Start time", value=0.0, key=f"{prefix}_start_time"),
            "max_value": max_val or None,
            "min_value": min_val or None,
        }
    elif stype == "sinusoid":
        return {
            "type": "sinusoid",
            "amplitude": st.number_input("Amplitude", value=0.5, key=f"{prefix}_amp"),
            "frequency": st.number_input("Frequency", value=0.05, key=f"{prefix}_freq"),
            "offset": st.number_input("Offset", value=1.0, key=f"{prefix}_offset"),
        }
    elif stype == "square":
        return {
            "type": "square",
            "amplitude": st.number_input("Amplitude", value=0.5, key=f"{prefix}_amp"),
            "frequency": st.number_input("Frequency", value=0.05, key=f"{prefix}_freq"),
            "duty_cycle": st.number_input("Duty cycle", value=0.5, min_value=0.0, max_value=1.0, key=f"{prefix}_duty"),
            "offset": st.number_input("Offset", value=1.0, key=f"{prefix}_offset"),
        }
    elif stype == "triangle":
        return {
            "type": "triangle",
            "amplitude": st.number_input("Amplitude", value=0.5, key=f"{prefix}_amp"),
            "frequency": st.number_input("Frequency", value=0.05, key=f"{prefix}_freq"),
            "offset": st.number_input("Offset", value=1.0, key=f"{prefix}_offset"),
        }
    elif stype in ("gaussian_noise", "uniform_noise"):
        return {
            "mean" if stype == "gaussian_noise" else "low": st.number_input(
                "Mean" if stype == "gaussian_noise" else "Low",
                value=0.0, key=f"{prefix}_a",
            ),
            "std" if stype == "gaussian_noise" else "high": st.number_input(
                "Std" if stype == "gaussian_noise" else "High",
                value=0.1, key=f"{prefix}_b",
            ),
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


def _parse_species_dict_optional(text: str) -> dict[str, int] | None:
    text = text.strip()
    if not text:
        return None
    return _parse_species_dict(text)


def prefill_session_state(cfg: dict) -> None:
    """Set st.session_state values from a saved config dict so that the
    config editor renders with pre-filled values (Edit Config flow)."""
    ss = st.session_state

    # species
    n_species = len(cfg.get("species", []))
    ss["n_species"] = n_species
    for i, sp in enumerate(cfg.get("species", [])):
        ss[f"species_{i}_name"] = sp.get("name", "A")
        ss[f"species_{i}_phase"] = sp.get("phase", "liquid")
        ss[f"species_{i}_qty"] = sp.get("initial_quantity", 0.0)

    # streams
    n_streams = len(cfg.get("streams", []))
    ss["n_streams"] = n_streams
    for i, sc in enumerate(cfg.get("streams", [])):
        ss[f"stream_{i}_name"] = sc.get("name", "feed")
        ss[f"stream_{i}_phase"] = sc.get("phase", "liquid")
        flow = sc.get("flow_signal", {"type": "constant", "value": 1.0})
        ftype = flow.get("type", "constant")
        ss[f"stream_{i}_flow_type"] = ftype
        _prefill_signal_params(ss, f"stream_{i}_flow", flow)
        comp = sc.get("composition", {})
        n_comp = len(comp)
        ss[f"stream_{i}_n_comp"] = n_comp
        for j, (sp_name, sig_spec) in enumerate(comp.items()):
            ss[f"stream_{i}_comp_{j}_sp"] = sp_name
            ctype = sig_spec.get("type", "constant")
            ss[f"stream_{i}_comp_{j}_type"] = ctype
            _prefill_signal_params(ss, f"stream_{i}_comp_{j}", sig_spec)
        ss[f"stream_{i}_active"] = sc.get("active", True)

    # reactions
    n_reactions = len(cfg.get("reactions", []))
    ss["n_reactions"] = n_reactions
    for i, rc in enumerate(cfg.get("reactions", [])):
        ss[f"reaction_{i}_reactants"] = _species_dict_to_str(rc.get("reactants", {}))
        ss[f"reaction_{i}_products"] = _species_dict_to_str(rc.get("products", {}))
        rk = rc.get("rate_constant", 0.1)
        ss[f"reaction_{i}_k"] = rk if isinstance(rk, (int, float)) else 0.1

    # decays
    n_decays = len(cfg.get("decays", []))
    ss["n_decays"] = n_decays
    for i, dc in enumerate(cfg.get("decays", [])):
        ss[f"decay_{i}_species"] = dc.get("species", "A")
        dk = dc.get("rate_constant", 0.1)
        ss[f"decay_{i}_k"] = dk if isinstance(dk, (int, float)) else 0.1
        ss[f"decay_{i}_phase"] = dc.get("phase", "liquid")
        ss[f"decay_{i}_products"] = _species_dict_to_str(dc.get("products", {}))

    # equilibria
    n_equilibria = len(cfg.get("equilibria", []))
    ss["n_equilibria"] = n_equilibria
    for i, ec in enumerate(cfg.get("equilibria", [])):
        ss[f"equilibrium_{i}_species"] = ec.get("species", "A")
        ss[f"equilibrium_{i}_evap"] = ec.get("evaporation_coeff", 0.1)
        ss[f"equilibrium_{i}_cond"] = ec.get("condensation_coeff", 0.1)

    # sensors
    n_sensors = len(cfg.get("sensors", []))
    ss["n_sensors"] = n_sensors
    for i, sn in enumerate(cfg.get("sensors", [])):
        ss[f"sensor_{i}_species"] = sn.get("species", "A")
        ss[f"sensor_{i}_phase"] = sn.get("phase", "liquid")
        noise = sn.get("noise", {"type": "gaussian_noise", "mean": 0.0, "std": 0.1})
        ss[f"sensor_{i}_noise_type"] = noise.get("type", "gaussian_noise")
        if noise.get("type") == "gaussian_noise":
            ss[f"sensor_{i}_noise_mean"] = noise.get("mean", 0.0)
            ss[f"sensor_{i}_noise_std"] = noise.get("std", 0.1)
        else:
            ss[f"sensor_{i}_noise_low"] = noise.get("low", -0.1)
            ss[f"sensor_{i}_noise_high"] = noise.get("high", 0.1)
        ss[f"sensor_{i}_key"] = sn.get("output_key", f"sensor_{i}")

    # reactor / outflow
    outflow = cfg.get("outflow_rate")
    if outflow is None:
        ss["outflow_mode"] = "constant_volume"
    elif isinstance(outflow, (int, float)):
        ss["outflow_mode"] = "fixed"
        ss["outflow_rate_fixed"] = float(outflow)
    else:
        ss["outflow_mode"] = "signal"
        sig_type = outflow.get("type", "constant")
        ss["outflow_signal_type"] = sig_type
        _prefill_signal_params(ss, "outflow_signal", outflow)

    # simulation
    ss["sim_dt"] = cfg.get("dt", 0.5)
    ss["sim_duration"] = cfg.get("duration", 20.0)
    ss["sim_seed"] = cfg.get("seed", 42)
    ss["sim_volume"] = cfg.get("volume", 1.0)


def _prefill_signal_params(ss: dict, prefix: str, spec: dict) -> None:
    stype = spec.get("type", "constant")
    if stype == "constant":
        ss[f"{prefix}_value"] = spec.get("value", 1.0)
    elif stype == "step":
        ss[f"{prefix}_baseline"] = spec.get("baseline", 0.0)
        ss[f"{prefix}_step_value"] = spec.get("step_value", 1.0)
        ss[f"{prefix}_step_time"] = spec.get("step_time", 5.0)
    elif stype == "ramp":
        ss[f"{prefix}_start_value"] = spec.get("start_value", 0.0)
        ss[f"{prefix}_slope"] = spec.get("slope", 0.1)
        ss[f"{prefix}_start_time"] = spec.get("start_time", 0.0)
        ss[f"{prefix}_max_value"] = spec.get("max_value") or 0.0
        ss[f"{prefix}_min_value"] = spec.get("min_value") or 0.0
    elif stype == "square":
        ss[f"{prefix}_amp"] = spec.get("amplitude", 0.5)
        ss[f"{prefix}_freq"] = spec.get("frequency", 0.05)
        ss[f"{prefix}_duty"] = spec.get("duty_cycle", 0.5)
        ss[f"{prefix}_offset"] = spec.get("offset", 1.0)
    elif stype in ("sinusoid", "triangle"):
        ss[f"{prefix}_amp"] = spec.get("amplitude", 0.5)
        ss[f"{prefix}_freq"] = spec.get("frequency", 0.05)
        ss[f"{prefix}_offset"] = spec.get("offset", 1.0)
    elif stype in ("gaussian_noise", "uniform_noise"):
        if stype == "gaussian_noise":
            ss[f"{prefix}_a"] = spec.get("mean", 0.0)
            ss[f"{prefix}_b"] = spec.get("std", 0.1)
        else:
            ss[f"{prefix}_a"] = spec.get("low", -0.1)
            ss[f"{prefix}_b"] = spec.get("high", 0.1)


def _validate_names(species_list: list[dict], stream_list: list[dict]) -> None:
    seen_species = {}
    for i, sp in enumerate(species_list):
        name = sp.get("name", "")
        if name in seen_species:
            st.warning(
                f"Duplicate species name \"{name}\" (species {seen_species[name]} "
                f"and {i}). The second definition will overwrite the first."
            )
        seen_species[name] = i

    seen_streams = {}
    for i, sc in enumerate(stream_list):
        name = sc.get("name", "")
        if name in seen_streams:
            st.warning(
                f"Duplicate stream name \"{name}\" (stream {seen_streams[name]} "
                f"and {i}). A feed stream with this name already exists — "
                "recorded data will be overwritten."
            )
        seen_streams[name] = i


def _species_dict_to_str(d: dict[str, int]) -> str:
    if not d:
        return ""
    return ",".join(f"{k}:{v}" for k, v in d.items())
