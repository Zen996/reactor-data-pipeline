"""Stage 5 demo: one ReactorState + one InputStream, run MixingProcess manually."""

from core.state import ReactorState
from core.stream import InputStream
from processes.mixing import MixingProcess
from signals.constant import Constant


def main() -> None:
    state = ReactorState(volume=100.0, time=0.0)
    state.register_species("A", phase="liquid", initial=50.0)
    state.register_species("B", phase="liquid", initial=30.0)

    feed = InputStream(
        name="Feed",
        flow_signal=Constant(10.0),
        composition={"A": Constant(2.0)},
        phase="liquid",
    )
    process = MixingProcess(streams=[feed])

    print(f"{'step':>4s}  {'time':>6s}  {'volume':>8s}  {'A':>8s}  {'B':>8s}  {'outflow':>8s}")
    print("-" * 50)
    for step in range(21):
        state.time = float(step)
        print(
            f"{step:4d}  {state.time:6.1f}  {state.volume:8.2f}  "
            f"{state.liquid.get('A', 0.0):8.2f}  {state.liquid.get('B', 0.0):8.2f}  "
            f"{state.outflow_rate:8.2f}"
        )
        process.execute(state, dt=1.0)


if __name__ == "__main__":
    main()
