"""Stage 2 demo: create a ReactorState, inspect and mutate it."""

from core.state import ReactorState


def main() -> None:
    state = ReactorState(time=0.0, volume=10.0)
    state.register_species("A", phase="liquid", initial=100.0)
    state.register_species("B", phase="vapor", initial=5.0)
    state.metadata["run_id"] = "demo-02"

    print("=== Initial snapshot ===")
    for k, v in state.snapshot().items():
        print(f"  {k}: {v}")

    print("\n--- Adding 20.0 of A (liquid) ---")
    state.add("A", 20.0)
    print(f"  A (liquid): {state.get('A')}")

    print("\n--- Adding -1.0 of B (vapor) ---")
    state.add("B", -1.0, phase="vapor")
    print(f"  B (vapor): {state.get('B', phase='vapor')}")

    print(f"\n=== Final snapshot ===")
    for k, v in state.snapshot().items():
        print(f"  {k}: {v}")

    print(f"\n  Total mass: {state.total_mass()}")
    print(f"  Liquid mass: {state.total_mass(phase='liquid')}")
    print(f"  Vapor mass: {state.total_mass(phase='vapor')}")
    print(f"  Concentration of A: {state.concentration('A'):.2f}")


if __name__ == "__main__":
    main()
