import csv
import json
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from vdkg.config import nemo_executable

_TYPED_LITERAL = re.compile(r'^"(.*)"\^\^<[^>]*#(\w+)>$')
_REPORT_LINE = re.compile(r"Derived (\d+) facts")


def parse_term(term: str) -> str | int | float:
    """Convert a term from Nemo's CSV export into a Python value."""
    if match := _TYPED_LITERAL.match(term):
        text, datatype = match.groups()
        return float(text) if datatype in {"double", "float", "decimal"} else int(text)
    if len(term) >= 2 and term[0] == term[-1] == '"':
        return term[1:-1]
    try:
        return int(term)
    except ValueError:
        return term


def read_export(path: Path) -> list[tuple]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [tuple(parse_term(term) for term in row) for row in csv.reader(handle)]


@dataclass
class ReasoningResult:
    relations: dict[str, list[tuple]]
    derived_facts: int
    seconds: float
    export_dir: Path | None = field(default=None, repr=False)
    trace: dict | None = field(default=None, repr=False)

    def __getitem__(self, predicate: str) -> list[tuple]:
        return self.relations.get(predicate, [])


class Nemo:
    def __init__(self, executable: Path | None = None):
        self.executable = executable or nemo_executable()

    def run(
        self,
        programs: list[Path],
        import_dir: Path,
        export_dir: Path | None = None,
        facts: str | None = None,
        trace: list[str] | None = None,
    ) -> ReasoningResult:
        """Run the concatenated programs; `trace` names facts whose derivation is recorded."""
        with tempfile.TemporaryDirectory(prefix="vdkg-nemo-") as scratch:
            scratch_dir = Path(scratch)
            target = export_dir or scratch_dir / "out"
            program = scratch_dir / "program.rls"
            parts = [p.read_text(encoding="utf-8") for p in programs] + [facts or ""]
            program.write_text("\n\n".join(parts), encoding="utf-8")
            trace_file = scratch_dir / "trace.json"
            command = [
                str(self.executable),
                str(program),
                "--import-dir",
                str(import_dir),
                "--export-dir",
                str(target),
                "--overwrite-results",
                "--report",
                "short",
            ]
            if trace:
                command += ["--trace", ";".join(trace), "--trace-output", str(trace_file)]

            started = time.perf_counter()
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            elapsed = time.perf_counter() - started
            if completed.returncode != 0:
                raise RuntimeError(f"Nemo failed:\n{completed.stderr or completed.stdout}")

            relations = {path.stem: read_export(path) for path in target.glob("*.csv")}
            derived = _REPORT_LINE.search(completed.stdout + completed.stderr)
            return ReasoningResult(
                relations=relations,
                derived_facts=int(derived.group(1)) if derived else 0,
                seconds=elapsed,
                export_dir=export_dir,
                trace=json.loads(trace_file.read_text(encoding="utf-8")) if trace else None,
            )
