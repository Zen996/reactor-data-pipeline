# Stage 7 — Physical Processes (Decay & Phase Equilibrium)

## Context

`ReactionProcess` (Stage 6) handles configurable stoichiometric reactions.
This stage adds two simpler, still-configurable physical processes: first
order decay, and liquid ⇌ vapor phase equilibrium.

## Files to Create

- `processes/decay.py`
- `processes/equilibrium.py`

## Public API

```python
# processes/decay.py
from dataclasses import dataclass, field
from core.process import Process

@dataclass
class DecayRule:
    species: str
    rate_constant: float
    phase: str = "liquid"
    products: dict[str, int] = field(default_factory=dict)
    """Optional: e.g. {"A": 2} for C -> 2A, or {} / {"Waste": 1} for a sink."""

class DecayProcess(Process):
    def __init__(self, rules: list[DecayRule]) -> None: ...
    def execute(self, state, dt: float) -> None: ...
```

```python
# processes/equilibrium.py
from dataclasses import dataclass
from core.process import Process

@dataclass
class PhaseEquilibrium:
    species: str
    evaporation_coeff: float
    condensation_coeff: float

class EquilibriumProcess(Process):
    def __init__(self, pairs: list[PhaseEquilibrium]) -> None: ...
    def execute(self, state, dt: float) -> None: ...
```

## Behavioral Requirements

### DecayProcess

1. First-order decay: `rate = rate_constant * concentration(species,
   phase)`; extent = `rate * dt`.
2. Decrease `species` by `extent * state.volume` (converted to quantity,
   consistent with the units convention chosen in Stage 6).
3. If `products` is non-empty, increase each product species by its
   stoichiometric share of the same extent (mirrors `ReactionProcess`
   stoichiometry handling — reuse a shared helper if convenient rather
   than duplicating the extent→quantity math).
4. Clamp at zero, same rationale as Stage 6.
5. Multiple `DecayRule`s affecting the same species accumulate correctly
   within one step (same order-independence requirement as Stage 6).

### EquilibriumProcess

1. Net transfer rate for a pair:
   `net = evaporation_coeff * concentration(species, "liquid")
        - condensation_coeff * concentration(species, "vapor")`.
   Positive `net` means liquid → vapor.
2. Apply `extent = net * dt` (quantity terms, volume-adjusted consistent
   with the rest of the codebase): decrease liquid by `extent`, increase
   vapor by `extent` (or the reverse if `net` is negative — it's the same
   line either way if signs are handled correctly).
3. Clamp so neither phase's quantity for that species goes negative.
4. A species that doesn't yet exist in the target phase should be
   auto-registered (same rationale as Stage 5's mixing auto-registration).

## Out of Scope

- Temperature/pressure dependence of any rate or equilibrium coefficient —
  explicitly future work per the project brief. Coefficients are constant
  numbers (or, from Stage 9 onward, stochastically varied — but that's
  additive, not something this stage builds).
- Any coupling between decay and equilibrium (e.g. a decaying vapor
  species) beyond what naturally falls out of both processes operating on
  the same shared `state` each step, in whatever order the process list
  specifies.

## Acceptance Criteria

`tests/processes/test_decay.py`:

1. Pure sink decay (no products): concentration follows the expected
   exponential decay curve over many steps (compare against the analytic
   `C0 * exp(-k*t)` within reasonable numerical-integration tolerance for
   a small `dt`).
2. Decay with products (`C -> 2A`): verify the 1:2 stoichiometric transfer
   ratio.
3. Clamps at zero rather than going negative when `dt` is deliberately
   made large relative to `rate_constant`.

`tests/processes/test_equilibrium.py`:

1. Starting with all liquid and no vapor, `evaporation_coeff > 0`,
   `condensation_coeff = 0`: vapor accumulates monotonically, liquid
   depletes monotonically.
2. Starting at the analytically-derived steady state (where
   `evaporation_coeff * liquid_conc == condensation_coeff * vapor_conc`),
   both phases stay approximately constant over many steps.
3. Starting with excess vapor and `condensation_coeff > 0`: net transfer
   correctly flows vapor → liquid.
4. Neither phase goes negative even with an aggressively large `dt`.

## Example

`examples/stage_07_demo.py`: one species undergoing decay into a second
species, plus a separate species undergoing liquid/vapor equilibrium, run
for enough steps to visually show exponential decay and equilibration.
