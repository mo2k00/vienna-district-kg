import argparse
import logging
import time
from collections.abc import Callable


def _ingest() -> None:
    from vdkg.ingest.pipeline import run

    run()


def _build() -> None:
    from vdkg.kg.build import run

    run()


def _reason() -> None:
    from vdkg.reasoning.materialize import run

    run()


def _embed() -> None:
    from vdkg.embeddings.pipeline import run

    run()


def _report() -> None:
    from vdkg.report.pipeline import run

    run()


def _serve(host: str, port: int) -> None:
    import uvicorn

    uvicorn.run("vdkg.api.main:app", host=host, port=port)


STEPS: dict[str, Callable[[], None]] = {
    "ingest": _ingest,
    "build": _build,
    "reason": _reason,
    "embed": _embed,
}


def main() -> None:
    parser = argparse.ArgumentParser(prog="vdkg", description="Vienna district knowledge graph")
    parser.add_argument("command", choices=[*STEPS, "all", "report", "serve"])
    parser.add_argument("--host", default="127.0.0.1", help="serve: interface to bind")
    parser.add_argument("--port", type=int, default=8000, help="serve: port")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")

    if args.command == "serve":
        _serve(args.host, args.port)
        return
    if args.command == "report":
        _report()
        return
    for name in STEPS if args.command == "all" else [args.command]:
        started = time.perf_counter()
        STEPS[name]()
        logging.getLogger("vdkg").info("%s finished in %.1fs", name, time.perf_counter() - started)


if __name__ == "__main__":
    main()
