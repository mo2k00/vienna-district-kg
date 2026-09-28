"""The materialised KG as (head, relation, tail) triples for embedding models.

Derived knowledge from the rules (feature levels, what districts offer, transit reachability) is
part of the training graph, so the embeddings learn from logic-completed facts.
"""

import pandas as pd

from vdkg.service.knowledge import KnowledgeBase

NEARBY_MINUTES = 10


def value_node(feature: str, level: str) -> str:
    return f"{feature}:{level}"


def build_triples(knowledge: KnowledgeBase) -> pd.DataFrame:
    rows: list[tuple[str, str, str]] = []
    for (district, feature), level in knowledge.levels.items():
        rows.append((district, f"has_{feature}", value_node(feature, level)))
    for district, neighbours in knowledge.neighbours.items():
        rows.extend((district, "adjacent_to", other) for other in neighbours)
    for district, preferences in knowledge.offers.items():
        rows.extend((district, "offers", f"pref:{p}") for p in preferences)
    for district, lines in knowledge.subway_lines.items():
        rows.extend((district, "served_by", f"line:{line}") for line in lines)
    for (a, b), minutes in knowledge.district_times.items():
        if a != b and minutes <= NEARBY_MINUTES:
            rows.append((a, "within_10_min_of", b))
    frame = pd.DataFrame(rows, columns=["head", "relation", "tail"]).drop_duplicates()
    return frame.sort_values(["relation", "head", "tail"]).reset_index(drop=True)
