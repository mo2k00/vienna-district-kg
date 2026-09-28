"""Derivation trees for selected facts, rendered as indented text."""

import re

from vdkg.config import KG_DIR, RULES
from vdkg.reasoning.materialize import PROGRAMS
from vdkg.reasoning.nemo import Nemo
from vdkg.service.knowledge import KnowledgeBase

_TYPED = re.compile(r'"([^"]*)"\^\^<[^>]+>')
MAX_DEPTH = 40
MAX_PREMISES = 3


_STATION = re.compile(r'"(at:\d+:\d+)"')


def _readable(term: str, stations: dict[str, str]) -> str:
    def shorten(match: re.Match) -> str:
        text = match.group(1)
        try:
            return f"{float(text):.4g}"
        except ValueError:
            return text

    def name(match: re.Match) -> str:
        station = match.group(1)
        return f'"{station}"' + (f" ({stations[station]})" if station in stations else "")

    return _STATION.sub(name, _TYPED.sub(shorten, term))


def traced_facts(knowledge: KnowledgeBase) -> list[str]:
    """An offers fact, a 2-of-3 signal fact and the recursive U1 ride Donaustadt → Karlsplatz.

    The ride fact is traced instead of `travelTime`: for `#min` aggregates Nemo reports an
    arbitrary witness, not necessarily the minimal one.
    """
    karlsplatz = next(s for s in knowledge.stations.values() if s.name == "Karlsplatz")
    hub = knowledge.hubs["d22"].id
    minutes = knowledge.travel_times[("d22", karlsplatz.id)]
    return [
        'offers("d07", "going_out")',
        'offers("d02", "green_quiet")',
        f'ride("{hub}", "{karlsplatz.id}", "U1", {minutes})',
    ]


def render(trace: dict, conclusion: str, stations: dict[str, str]) -> str:
    by_conclusion = {step["conclusion"]: step for step in trace["inferences"]}
    lines: list[str] = []

    def visit(fact: str, depth: int, seen: frozenset[str]) -> None:
        step = by_conclusion.get(fact)
        indent = "  " * depth
        if step is None or step["rule"] == "Asserted":
            lines.append(f"{indent}{_readable(fact, stations)}   [fact]")
            return
        lines.append(f"{indent}{_readable(fact, stations)}")
        lines.append(f"{indent}  ⟵ {_readable(step['rule'], stations)}")
        if depth >= MAX_DEPTH or fact in seen:
            lines.append(f"{indent}    …")
            return
        premises = step["premises"]
        for premise in premises[:MAX_PREMISES]:
            visit(premise, depth + 2, seen | {fact})
        if len(premises) > MAX_PREMISES:
            lines.append(f"{indent}    … {len(premises) - MAX_PREMISES} more premises")

    visit(conclusion, 0, frozenset())
    return "\n".join(lines)


def run(knowledge: KnowledgeBase) -> dict[str, str]:
    facts = traced_facts(knowledge)
    result = Nemo().run([RULES / name for name in PROGRAMS], KG_DIR, trace=facts)
    stations = {s.id: s.name for s in knowledge.stations.values()}
    return {fact: render(result.trace, fact, stations) for fact in facts}
