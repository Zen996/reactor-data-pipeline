"""Stage 3 demo: build the brief's composite example and print values."""

from signals.constant import Constant
from signals.step import Step
from signals.sinusoid import Sinusoid
from signals.composite import CompositeSignal


def main() -> None:
    c = CompositeSignal([
        (0.0, 100.0, Constant(5.0)),
        (100.0, 250.0, Step(baseline=0.0, step_value=10.0, step_time=100.0)),
        (250.0, 500.0, Sinusoid(amplitude=2.0, frequency=0.01, offset=3.0)),
    ])

    print("t\tvalue")
    print("--\t-----")
    for t in range(0, 500, 25):
        print(f"{t}\t{c.value(t):.4f}")


if __name__ == "__main__":
    main()
