"""Preset configurations for quick-start and testing.

Each preset is a dict that matches the ``SimulationConfig.from_dict()``
schema, so it can be used both in tests (via ``SimulationConfig.from_dict``)
and in the GUI (via ``prefill_session_state``).
"""

PRESETS: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# 1. First-order reaction A → B (constant feed)
# ---------------------------------------------------------------------------

PRESETS["first_order_constant"] = {
    "species": [
        {"name": "A", "phase": "liquid", "initial_quantity": 0.0},
        {"name": "B", "phase": "liquid", "initial_quantity": 0.0},
    ],
    "streams": [
        {
            "name": "feed",
            "phase": "liquid",
            "flow_signal": {"type": "constant", "value": 0.5},
            "composition": {"A": {"type": "constant", "value": 2.0}},
            "active": True,
        }
    ],
    "reactions": [
        {"reactants": {"A": 1}, "products": {"B": 1}, "rate_constant": 0.2}
    ],
    "decays": [],
    "equilibria": [],
    "manipulations": [],
    "sensors": [],
    "dt": 0.5,
    "duration": 30.0,
    "seed": 42,
    "max_volume": 1.0,
    "min_volume": 0.0,
    "outflow_rate": None,
}

# ---------------------------------------------------------------------------
# 2. First-order reaction A → B (step feed)
# ---------------------------------------------------------------------------

PRESETS["first_order_step"] = {
    "species": [
        {"name": "A", "phase": "liquid", "initial_quantity": 10.0},
        {"name": "B", "phase": "liquid", "initial_quantity": 0.0},
    ],
    "streams": [
        {
            "name": "feed",
            "phase": "liquid",
            "flow_signal": {
                "type": "step",
                "baseline": 0.0,
                "step_value": 0.5,
                "step_time": 5.0,
            },
            "composition": {"A": {"type": "constant", "value": 1.0}},
            "active": True,
        }
    ],
    "reactions": [
        {"reactants": {"A": 1}, "products": {"B": 1}, "rate_constant": 0.15}
    ],
    "decays": [],
    "equilibria": [],
    "manipulations": [],
    "sensors": [],
    "dt": 0.5,
    "duration": 40.0,
    "seed": 42,
    "max_volume": 1.0,
    "min_volume": 0.0,
    "outflow_rate": None,
}

# ---------------------------------------------------------------------------
# 3. First-order reaction A → B (ramp feed)
# ---------------------------------------------------------------------------

PRESETS["first_order_ramp"] = {
    "species": [
        {"name": "A", "phase": "liquid", "initial_quantity": 0.0},
        {"name": "B", "phase": "liquid", "initial_quantity": 0.0},
    ],
    "streams": [
        {
            "name": "feed",
            "phase": "liquid",
            "flow_signal": {
                "type": "ramp",
                "start_value": 0.0,
                "slope": 0.05,
                "start_time": 0.0,
            },
            "composition": {"A": {"type": "constant", "value": 1.0}},
            "active": True,
        }
    ],
    "reactions": [
        {"reactants": {"A": 1}, "products": {"B": 1}, "rate_constant": 0.2}
    ],
    "decays": [],
    "equilibria": [],
    "manipulations": [],
    "sensors": [],
    "dt": 0.5,
    "duration": 40.0,
    "seed": 42,
    "max_volume": 1.0,
    "min_volume": 0.0,
    "outflow_rate": None,
}

# ---------------------------------------------------------------------------
# 4. First-order reaction A → B (sinusoid feed)
# ---------------------------------------------------------------------------

PRESETS["first_order_sinusoid"] = {
    "species": [
        {"name": "A", "phase": "liquid", "initial_quantity": 0.0},
        {"name": "B", "phase": "liquid", "initial_quantity": 0.0},
    ],
    "streams": [
        {
            "name": "feed",
            "phase": "liquid",
            "flow_signal": {
                "type": "sinusoid",
                "amplitude": 0.3,
                "frequency": 0.05,
                "offset": 0.5,
            },
            "composition": {"A": {"type": "constant", "value": 1.0}},
            "active": True,
        }
    ],
    "reactions": [
        {"reactants": {"A": 1}, "products": {"B": 1}, "rate_constant": 0.2}
    ],
    "decays": [],
    "equilibria": [],
    "manipulations": [],
    "sensors": [],
    "dt": 0.5,
    "duration": 40.0,
    "seed": 42,
    "max_volume": 1.0,
    "min_volume": 0.0,
    "outflow_rate": None,
}

# ---------------------------------------------------------------------------
# 5. Second-order reaction 2A → B
# ---------------------------------------------------------------------------

PRESETS["second_order_2A_to_B"] = {
    "species": [
        {"name": "A", "phase": "liquid", "initial_quantity": 10.0},
        {"name": "B", "phase": "liquid", "initial_quantity": 0.0},
    ],
    "streams": [
        {
            "name": "feed",
            "phase": "liquid",
            "flow_signal": {"type": "constant", "value": 0.3},
            "composition": {"A": {"type": "constant", "value": 1.0}},
            "active": True,
        }
    ],
    "reactions": [
        {"reactants": {"A": 2}, "products": {"B": 1}, "rate_constant": 0.05}
    ],
    "decays": [],
    "equilibria": [],
    "manipulations": [],
    "sensors": [],
    "dt": 0.5,
    "duration": 40.0,
    "seed": 42,
    "max_volume": 1.0,
    "min_volume": 0.0,
    "outflow_rate": None,
}

# ---------------------------------------------------------------------------
# 6. Second-order reaction A + B → C (two feeds)
# ---------------------------------------------------------------------------

PRESETS["second_order_A_plus_B"] = {
    "species": [
        {"name": "A", "phase": "liquid", "initial_quantity": 0.0},
        {"name": "B", "phase": "liquid", "initial_quantity": 0.0},
        {"name": "C", "phase": "liquid", "initial_quantity": 0.0},
    ],
    "streams": [
        {
            "name": "feed_A",
            "phase": "liquid",
            "flow_signal": {"type": "constant", "value": 0.5},
            "composition": {"A": {"type": "constant", "value": 1.0}},
            "active": True,
        },
        {
            "name": "feed_B",
            "phase": "liquid",
            "flow_signal": {"type": "constant", "value": 0.5},
            "composition": {"B": {"type": "constant", "value": 1.0}},
            "active": True,
        },
    ],
    "reactions": [
        {
            "reactants": {"A": 1, "B": 1},
            "products": {"C": 1},
            "rate_constant": 0.15,
        }
    ],
    "decays": [],
    "equilibria": [],
    "manipulations": [],
    "sensors": [],
    "dt": 0.5,
    "duration": 30.0,
    "seed": 42,
    "max_volume": 1.0,
    "min_volume": 0.0,
    "outflow_rate": None,
}

# ---------------------------------------------------------------------------
# 7. First-order decay A → (decay) with product B
# ---------------------------------------------------------------------------

PRESETS["decay_with_product"] = {
    "species": [
        {"name": "A", "phase": "liquid", "initial_quantity": 50.0},
        {"name": "B", "phase": "liquid", "initial_quantity": 0.0},
    ],
    "streams": [
        {
            "name": "feed",
            "phase": "liquid",
            "flow_signal": {"type": "constant", "value": 0.2},
            "composition": {"A": {"type": "constant", "value": 1.0}},
            "active": True,
        }
    ],
    "reactions": [],
    "decays": [
        {
            "species": "A",
            "rate_constant": 0.1,
            "phase": "liquid",
            "products": {"B": 1},
        }
    ],
    "equilibria": [],
    "manipulations": [],
    "sensors": [],
    "dt": 0.5,
    "duration": 30.0,
    "seed": 42,
    "max_volume": 1.0,
    "min_volume": 0.0,
    "outflow_rate": None,
}

# ---------------------------------------------------------------------------
# 8. Vapor equilibrium
# ---------------------------------------------------------------------------

PRESETS["vapor_equilibrium"] = {
    "species": [
        {"name": "X", "phase": "liquid", "initial_quantity": 10.0},
        {"name": "X", "phase": "vapor", "initial_quantity": 1.0},
    ],
    "streams": [
        {
            "name": "feed",
            "phase": "liquid",
            "flow_signal": {"type": "constant", "value": 0.3},
            "composition": {"X": {"type": "constant", "value": 1.0}},
            "active": True,
        }
    ],
    "reactions": [],
    "decays": [],
    "equilibria": [
        {
            "species": "X",
            "evaporation_coeff": 0.2,
            "condensation_coeff": 0.1,
        }
    ],
    "manipulations": [],
    "sensors": [],
    "dt": 0.5,
    "duration": 30.0,
    "seed": 42,
    "max_volume": 1.0,
    "min_volume": 0.0,
    "outflow_rate": None,
}
