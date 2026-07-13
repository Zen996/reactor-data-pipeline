from __future__ import annotations

import os
from typing import Any

from dataclasses import dataclass, field

from config.simulation import SimulationConfig, StreamConfig
from core.engine import SimulationEngine
from core.random_manager import RandomManager
from core.state import ReactorState
from core.stream import InputStream
from processes.decay import DecayProcess, DecayRule
from processes.equilibrium import EquilibriumProcess, PhaseEquilibrium
from processes.manipulation import (
    DrainReactor,
    InjectSpecies,
    Manipulation,
    ManipulationProcess,
    PeriodicTrigger,
    RemoveSpecies,
    ThresholdTrigger,
    TimeTrigger,
    VentVapor,
)
from processes.mixing import MixingProcess
from processes.reaction import Reaction, ReactionProcess
from processes.sensors import SensorNoiseProcess, SensorSpec
from recorder.recorder import TabularRecorder
from signals.base import Signal
from signals.composite import CompositeSignal
from signals.constant import Constant
from signals.noise import GaussianNoise, UniformNoise
from signals.ramp import Ramp
from signals.sinusoid import Sinusoid, SquareWave, TriangleWave
from signals.step import Step


@dataclass
class BuiltExperiment:
    config: SimulationConfig
    state: ReactorState
    engine: SimulationEngine
    random_manager: RandomManager
    streams: list
    reactions: list
    decays: list
    equilibria: list
    manipulations: list
    recorder: TabularRecorder


def build_experiment(config: SimulationConfig) -> BuiltExperiment:
    """Same assembly as build_engine, but shares object references so live
    tweaks via BuiltExperiment attributes affect running processes."""
    rm = RandomManager(config.seed) if config.seed is not None else RandomManager(None)

    state = ReactorState()
    state.volume = config.volume
    for sp in config.species:
        state.register_species(sp.name, sp.phase, sp.initial_quantity)

    streams: list[InputStream] = []
    _normalized_streams = [_as_dataclass(StreamConfig, s) for s in config.streams]
    for sc in _normalized_streams:
        flow_sig = build_signal(sc.flow_signal, rm, f"stream.{sc.name}.flow")
        comp = {
            species: build_signal(sig_spec, rm, f"stream.{sc.name}.comp.{species}")
            for species, sig_spec in sc.composition.items()
        }
        stream = InputStream(
            name=sc.name,
            flow_signal=flow_sig,
            composition=comp,
            phase=sc.phase,
            active=sc.active,
        )
        streams.append(stream)

    processes: list = []

    outflow_rate: Signal | float | None = None
    if isinstance(config.outflow_rate, dict):
        outflow_rate = build_signal(config.outflow_rate, rm, "outflow")
    else:
        outflow_rate = config.outflow_rate
    processes.append(MixingProcess(streams=streams, outflow_rate=outflow_rate))

    reactions: list[Reaction] = []
    for rc in config.reactions:
        k: float | Signal = rc.rate_constant
        if isinstance(k, dict):
            k = build_signal(k, rm, f"reaction.{_reactants_str(rc.reactants)}.k")
        reactions.append(
            Reaction(
                reactants=dict(rc.reactants),
                products=dict(rc.products),
                rate_constant=k,
                order=dict(rc.order) if rc.order else None,
                phase=rc.phase,
            )
        )
    if reactions:
        processes.append(ReactionProcess(reactions))

    decays: list = []
    for dc in config.decays:
        k: float | Signal = dc.rate_constant
        if isinstance(k, dict):
            k = build_signal(k, rm, f"decay.{dc.species}.k")
        decays.append(
            DecayRule(
                species=dc.species,
                rate_constant=k,
                phase=dc.phase,
                products=dict(dc.products) if dc.products else None,
            )
        )
    if decays:
        processes.append(DecayProcess(decays))

    equilibria: list = []
    for ec in config.equilibria:
        equilibria.append(
            PhaseEquilibrium(
                species=ec.species,
                evaporation_coeff=ec.evaporation_coeff,
                condensation_coeff=ec.condensation_coeff,
            )
        )
    if equilibria:
        processes.append(EquilibriumProcess(equilibria))

    manipulations: list[Manipulation] = []
    for mspec in config.manipulations:
        trigger_spec = dict(mspec["trigger"])
        action_spec = dict(mspec["action"])
        ttype = trigger_spec.pop("type")
        trigger_cls = TRIGGER_REGISTRY[ttype]
        atype = action_spec.pop("type")
        action_cls = ACTION_REGISTRY[atype]
        trigger = trigger_cls(**trigger_spec)
        action = action_cls(**action_spec)
        manipulations.append(
            Manipulation(
                trigger=trigger,
                action=action,
                one_shot=mspec.get("one_shot", False),
            )
        )
    if manipulations:
        processes.append(ManipulationProcess(manipulations))

    if config.sensors:
        sensor_specs = []
        for ss in config.sensors:
            noise_sig = build_signal(ss["noise"], rm, f"sensor.{ss['output_key']}.noise")
            sensor_specs.append(
                SensorSpec(
                    species=ss["species"],
                    phase=ss.get("phase", "liquid"),
                    noise=noise_sig,
                    output_key=ss["output_key"],
                )
            )
        processes.append(SensorNoiseProcess(sensor_specs))

    recorder = TabularRecorder(run_metadata={
        "dt": config.dt, "duration": config.duration,
        "seed": config.seed, "species": [s.name for s in config.species],
    })

    engine = SimulationEngine(
        initial_state=state,
        processes=processes,
        recorder=recorder,
        dt=config.dt,
        duration=config.duration,
    )

    return BuiltExperiment(
        config=config, state=state, engine=engine, random_manager=rm,
        streams=streams, reactions=reactions, decays=decays,
        equilibria=equilibria, manipulations=manipulations, recorder=recorder,
    )


def _as_dataclass(cls, item):
    if isinstance(item, cls):
        return item
    return cls(**item)


SIGNAL_REGISTRY: dict[str, type] = {
    "constant": Constant,
    "step": Step,
    "ramp": Ramp,
    "sinusoid": Sinusoid,
    "square": SquareWave,
    "triangle": TriangleWave,
    "gaussian_noise": GaussianNoise,
    "uniform_noise": UniformNoise,
    "composite": CompositeSignal,
}

TRIGGER_REGISTRY: dict[str, type] = {
    "time": TimeTrigger,
    "threshold": ThresholdTrigger,
    "periodic": PeriodicTrigger,
}

ACTION_REGISTRY: dict[str, type] = {
    "vent_vapor": VentVapor,
    "remove_species": RemoveSpecies,
    "inject": InjectSpecies,
    "drain": DrainReactor,
}


def build_signal(
    spec: dict,
    random_manager: RandomManager | None = None,
    name: str = "",
) -> Signal:
    spec_type = spec["type"]
    cls = SIGNAL_REGISTRY[spec_type]
    params: dict[str, Any] = {k: v for k, v in spec.items() if k != "type"}

    if spec_type in ("gaussian_noise", "uniform_noise"):
        params.pop("seed", None)
        if random_manager is not None:
            params["generator"] = random_manager.spawn(name)
        return cls(**params)

    if spec_type == "composite":
        segments = []
        for seg in params["segments"]:
            sub_name = f"{name}.seg_{seg['start']}"
            sig = build_signal(seg["signal"], random_manager, sub_name)
            segments.append((seg["start"], seg["end"], sig))
        return cls(segments=segments)

    return cls(**params)


def build_engine(config: SimulationConfig) -> SimulationEngine:
    rm = RandomManager(config.seed) if config.seed is not None else RandomManager(None)

    state = ReactorState()
    state.volume = config.volume
    for sp in config.species:
        state.register_species(sp.name, sp.phase, sp.initial_quantity)

    streams = []
    _normalized_streams = [_as_dataclass(StreamConfig, s) for s in config.streams]
    for sc in _normalized_streams:
        flow_sig = build_signal(
            sc.flow_signal, rm, f"stream.{sc.name}.flow"
        )
        comp = {
            species: build_signal(sig_spec, rm, f"stream.{sc.name}.comp.{species}")
            for species, sig_spec in sc.composition.items()
        }
        stream = InputStream(
            name=sc.name,
            flow_signal=flow_sig,
            composition=comp,
            phase=sc.phase,
            active=sc.active,
        )
        streams.append(stream)

    processes = []

    outflow_rate: Signal | float | None = None
    if isinstance(config.outflow_rate, dict):
        outflow_rate = build_signal(config.outflow_rate, rm, "outflow")
    else:
        outflow_rate = config.outflow_rate
    processes.append(MixingProcess(streams=streams, outflow_rate=outflow_rate))

    if config.reactions:
        reactions = []
        for rc in config.reactions:
            k: float | Signal = rc.rate_constant
            if isinstance(k, dict):
                k = build_signal(k, rm, f"reaction.{_reactants_str(rc.reactants)}.k")
            reactions.append(
                Reaction(
                    reactants=dict(rc.reactants),
                    products=dict(rc.products),
                    rate_constant=k,
                    order=dict(rc.order) if rc.order else None,
                    phase=rc.phase,
                )
            )
        processes.append(ReactionProcess(reactions))

    if config.decays:
        rules = []
        for dc in config.decays:
            k: float | Signal = dc.rate_constant
            if isinstance(k, dict):
                k = build_signal(k, rm, f"decay.{dc.species}.k")
            rules.append(
                DecayRule(
                    species=dc.species,
                    rate_constant=k,
                    phase=dc.phase,
                    products=dict(dc.products) if dc.products else None,
                )
            )
        processes.append(DecayProcess(rules))

    if config.equilibria:
        eqs = []
        for ec in config.equilibria:
            eqs.append(
                PhaseEquilibrium(
                    species=ec.species,
                    evaporation_coeff=ec.evaporation_coeff,
                    condensation_coeff=ec.condensation_coeff,
                )
            )
        processes.append(EquilibriumProcess(eqs))

    if config.manipulations:
        manip_list = []
        for mspec in config.manipulations:
            trigger_spec = dict(mspec["trigger"])
            action_spec = dict(mspec["action"])
            ttype = trigger_spec.pop("type")
            trigger_cls = TRIGGER_REGISTRY[ttype]
            atype = action_spec.pop("type")
            action_cls = ACTION_REGISTRY[atype]
            trigger = trigger_cls(**trigger_spec)
            action = action_cls(**action_spec)
            manip_list.append(
                Manipulation(
                    trigger=trigger,
                    action=action,
                    one_shot=mspec.get("one_shot", False),
                )
            )
        processes.append(ManipulationProcess(manip_list))

    if config.sensors:
        sensor_specs = []
        for ss in config.sensors:
            noise_sig = build_signal(
                ss["noise"], rm, f"sensor.{ss['output_key']}.noise"
            )
            sensor_specs.append(
                SensorSpec(
                    species=ss["species"],
                    phase=ss.get("phase", "liquid"),
                    noise=noise_sig,
                    output_key=ss["output_key"],
                )
            )
        processes.append(SensorNoiseProcess(sensor_specs))

    recorder = TabularRecorder(run_metadata={
        "dt": config.dt,
        "duration": config.duration,
        "seed": config.seed,
        "species": [s.name for s in config.species],
    })

    engine = SimulationEngine(
        initial_state=state,
        processes=processes,
        recorder=recorder,
        dt=config.dt,
        duration=config.duration,
    )
    engine._config_recorder = recorder
    engine._config_output = config.recorder_output
    return engine


def run_and_export(engine: SimulationEngine) -> None:
    engine.run()
    recorder: TabularRecorder = engine._config_recorder
    out = engine._config_output
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        recorder.export_csv(out + ".csv")
        recorder.export_parquet(out + ".parquet")
        recorder.export_metadata(out + ".json")


def _reactants_str(reactants: dict[str, int]) -> str:
    return "_".join(f"{k}{v}" for k, v in sorted(reactants.items()))
