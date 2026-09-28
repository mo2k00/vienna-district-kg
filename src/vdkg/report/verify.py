"""Independent checks of reasoning results against plain Python implementations."""

import heapq
from collections import defaultdict

from vdkg.config import KG_DIR
from vdkg.kg import schema
from vdkg.kg.store import read_relation
from vdkg.service.knowledge import KnowledgeBase

TRANSFER_MINUTES = 4
LIMIT_MINUTES = 45


def _line_aware_times(hub: str, segments: dict[str, list[tuple[str, str, int]]]) -> dict[str, int]:
    """Shortest bounded travel times from `hub` over (station, line) states with transfer cost."""
    best: dict[tuple[str, str], int] = {}
    queue: list[tuple[int, str, str]] = []
    for target, line, minutes in segments[hub]:
        if minutes <= LIMIT_MINUTES:
            heapq.heappush(queue, (minutes, target, line))
    while queue:
        cost, station, line = heapq.heappop(queue)
        if best.get((station, line), LIMIT_MINUTES + 1) <= cost:
            continue
        best[(station, line)] = cost
        for target, next_line, minutes in segments[station]:
            total = cost + minutes + (TRANSFER_MINUTES if next_line != line else 0)
            if total <= LIMIT_MINUTES and best.get((target, next_line), LIMIT_MINUTES + 1) > total:
                heapq.heappush(queue, (total, target, next_line))
    times: dict[str, int] = {hub: 0}
    for (station, _), cost in best.items():
        if station != hub:
            times[station] = min(cost, times.get(station, cost))
    return times


def travel_times(knowledge: KnowledgeBase) -> dict:
    frame = read_relation(schema.SEGMENT, KG_DIR)
    segments: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    for row in frame.itertuples(index=False):
        segments[row.from_station].append((row.to_station, row.line, int(row.minutes)))

    reasoned = knowledge.travel_times
    compared = mismatches = 0
    examples = []
    for district, hub in knowledge.hubs.items():
        reference = _line_aware_times(hub.id, segments)
        keys = set(reference) | {s for (d, s) in reasoned if d == district}
        for station in keys:
            compared += 1
            if reasoned.get((district, station)) != reference.get(station):
                mismatches += 1
                if len(examples) < 5:
                    examples.append(
                        (
                            district,
                            station,
                            reasoned.get((district, station)),
                            reference.get(station),
                        )
                    )
    return {"compared": compared, "mismatches": mismatches, "examples": examples}


def ranks(knowledge: KnowledgeBase) -> dict:
    compared = mismatches = 0
    for district, features in knowledge.features.items():
        for feature, value in features.items():
            expected = sum(1 for other in knowledge.features.values() if other[feature] < value)
            compared += 1
            mismatches += knowledge.ranks[(district, feature)] != expected
    return {"compared": compared, "mismatches": mismatches}


def sport_venues(knowledge: KnowledgeBase) -> dict:
    """Venue count per (district, sport) via union-find over the candidate matches."""
    sports = read_relation(schema.POI_SPORT, KG_DIR)
    matches = read_relation(schema.POI_MATCH, KG_DIR)
    parent: dict[tuple[int, str], tuple[int, str]] = {}

    def find(node):
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for row in sports.itertuples(index=False):
        find((row.id, row.sport))
    for row in matches.itertuples(index=False):
        a, b = find((row.id_a, row.sport)), find((row.id_b, row.sport))
        if a != b:
            parent[max(a, b)] = min(a, b)

    district_of = {(row.id, row.sport): row.district for row in sports.itertuples(index=False)}
    expected: dict[tuple[str, str], int] = defaultdict(int)
    for node in {find(n) for n in district_of}:
        expected[(district_of[node], node[1])] += 1

    reasoned = {
        (district, key.removeprefix("sport:")): count
        for district, counts in knowledge.venue_counts.items()
        for key, count in counts.items()
        if key.startswith("sport:") and count
    }
    return {
        "venues_python": sum(expected.values()),
        "venues_rules": sum(reasoned.values()),
        "mismatches": sum(
            expected.get(k, 0) != reasoned.get(k, 0) for k in set(expected) | set(reasoned)
        ),
    }


def run(knowledge: KnowledgeBase) -> dict:
    return {
        "travel_times": travel_times(knowledge),
        "ranks": ranks(knowledge),
        "sport_venues": sport_venues(knowledge),
    }
