# Known Issues & Scope Notes

## Reactions and decays are liquid-phase only (intentional scope)

`ReactionProcess` (processes/reaction.py) and `DecayProcess`
(processes/decay.py) apply all product/decay deltas to the `"liquid"`
phase regardless of the reaction/rule's `phase` setting.  The rate
calculation correctly reads concentrations from the configured phase, so
reactant depletion is phase-accurate, but products land in liquid.

`ReactionConfig.phase` and `DecayConfig.phase` exist in the config schema
and are passed through to the process objects, but the accumulation loop
(`dict[str, float]` with no phase tracking) ignores them for product
output.

This is an accepted scope limitation: chemical transformations are
assumed liquid-phase.  Extending to vapor-phase or multi-phase reactions
would require per-phase accumulation in the process loops.
