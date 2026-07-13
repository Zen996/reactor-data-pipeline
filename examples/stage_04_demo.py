"""Stage 4 demo: two streams — constant base feed + step disturbance feed."""

from core.stream import InputStream
from signals.constant import Constant
from signals.step import Step


def main() -> None:
    base_feed = InputStream(
        name="Base Feed",
        flow_signal=Constant(2.0),
        composition={"A": Constant(5.0)},
        phase="liquid",
    )
    disturbance = InputStream(
        name="Disturbance Feed",
        flow_signal=Step(baseline=0.0, step_value=3.0, step_time=50.0),
        composition={"B": Constant(10.0)},
        phase="liquid",
    )

    streams = [base_feed, disturbance]
    print(f"{'t':>4s}  {'stream':20s}  {'flow':>6s}  {'inflow A':>8s}  {'inflow B':>8s}")
    print("-" * 52)
    for t in range(0, 101, 10):
        for s in streams:
            inflow = s.species_inflow(t)
            print(
                f"{t:4d}  {s.name:20s}  {s.flow_rate(t):6.1f}  "
                f"{inflow.get('A', 0.0):8.1f}  {inflow.get('B', 0.0):8.1f}"
            )


if __name__ == "__main__":
    main()
