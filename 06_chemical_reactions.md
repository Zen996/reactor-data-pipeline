# Stage 6 — Chemical Reactions

## Context

`MixingProcess` (Stage 5) moves material in and out of the tank. Now add
the ability to transform species into each other inside the tank, via
arbitrary configurable reactions — no reaction is ever hardcoded into the
process itself.

## Files to Create

- `processes/reaction.py`

## Public API

```python
# processes/reaction.py
from dataclasses import dataclass
from core.process import Process

@dataclass
class Reaction:
    reactants: dict[str, int]   # species -> stoichiometric coefficient, e.g. {"A": 2, "B": 1}
    products: dict[str, int]    # species -> stoichiometric coefficient, e.g. {"C": 3}
    rate_constant: float
    order: dict[str, float] | None = None
    """Reaction order per species for the rate law. If None, defaults to
    using the reactant stoichiometric coefficients as the kinetic order
    (elementary-reaction assumption) — document this default explicitly,
    since it's a simplification, not a chemistry fact."""
    phase: str = "liquid"  # reactions occur within one phase for now

class ReactionProcess(Process):
    def __init__(self, reactions: list[Reaction]) -> None: ...

    def execute(self, state, dt: float) -> None: ...
```

## Behavioral Requirements

1. For each reaction, compute the rate:
   `rate = rate_constant * product(concentration(species)^order[species]
   for species in reactants)`.
2. Extent of reaction this step: `extent = rate * dt` (in concentration
   units — keep it simple, no separate "rate per volume vs. per mass"
   distinction unless you want to note it as a future refinement).
3. Apply stoichiometry: each reactant's quantity decreases by
   `coefficient * extent * state.volume` (converting concentration extent
   back to quantity — be explicit and consistent about whether reactions
   operate on concentrations or absolute quantities internally; pick one,
   document it, and keep `ReactionProcess` and `state.add()` units
   consistent). Each product's quantity increases by
   `coefficient * extent * state.volume`.
4. Multiple reactions in the list are summed independently per species
   (a species can be a reactant in one reaction and a product in
   another within the same step) — accumulate all deltas per species
   before applying them to `state`, so reaction order in the list doesn't
   change the result within a single timestep (this matters: don't apply
   reaction 1's effect to `state` before computing reaction 2's rate from
   stale vs. fresh concentrations — pick "all rates computed from the
   start-of-step state" as the consistent, order-independent convention).
5. Clamp resulting quantities at zero — a reaction must never drive a
   species negative; if the naive extent would do so, cap the extent at
   the amount available (this is a simplification flagged in the project
   brief: "prioritize stable and understandable behavior over physical
   realism").
6. Record something useful per reaction into `state.derived` (e.g.
   `derived["reaction_rate_0"] = rate`) so Stage 10's recorder can capture
   reaction rates as the brief requires — use a stable naming scheme (e.g.
   index-based `reaction_rate_{i}`, or a `name` field added to `Reaction`
   for a friendlier key — agent's choice, document it).
7. No reaction, species name, or stoichiometry may be hardcoded in
   `processes/reaction.py` itself — everything must come from the
   `Reaction` objects passed in.

## Out of Scope

- Decay and equilibrium (Stage 7) — those are separate process types even
  though decay is arguably "just a reaction with one reactant." Keep them
  separate per the architecture; you may internally reuse rate-law helper
  functions between the two files if that avoids duplication, but they
  stay distinct `Process` classes.
- Manipulations (Stage 8) or manual mid-run reaction rate changes — a
  reaction's `rate_constant` is fixed for this stage (Stage 9 will let it
  vary stochastically).

## Acceptance Criteria

`tests/processes/test_reaction.py`:

1. The brief's example reaction `2A + B → 3C` with a simple rate constant:
   starting from known concentrations, verify after one step that A, B,
   and C moved in the correct 2:1:3 stoichiometric ratio relative to each
   other (the ratio of *changes*, not raw values).
2. A species not involved in any reaction is untouched.
3. Two reactions sharing a common species — verify the net change equals
   the sum of both reactions' individual contributions, and that this
   sum doesn't depend on the reactions' order in the list.
4. Starting a reactant near zero concentration with a rate that would
   naively drive it negative — verify it clamps at zero rather than going
   negative.
5. `order=None` defaults to using stoichiometric coefficients as reaction
   order — verify by comparing against an explicit `order=` reaction with
   the same coefficients.
6. `state.derived` contains a recognizable rate value per reaction after
   `execute()`.

## Example

`examples/stage_06_demo.py`: set up `2A + B → 3C` with realistic starting
concentrations, run several steps via the Stage 1 engine (with only
`ReactionProcess` in the pipeline, no mixing yet), print concentrations of
A, B, C over time to show the expected depletion/formation curve.
