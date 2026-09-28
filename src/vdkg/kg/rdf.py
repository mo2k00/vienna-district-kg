"""Export the KG as RDF (TriG): ground facts and rule-derived facts in separate named graphs."""

from urllib.parse import quote

import pandas as pd
from rdflib import RDF, RDFS, XSD, Dataset, Literal, Namespace, URIRef

from vdkg.config import KG_DIR, PROCESSED
from vdkg.kg import schema
from vdkg.kg.store import read_relation
from vdkg.service.catalogue import FEATURE_LABELS, PREFERENCES
from vdkg.service.knowledge import KnowledgeBase

VKG = Namespace("http://example.org/vienna-kg/")
GROUND = URIRef(VKG["graph/ground"])
DERIVED = URIRef(VKG["graph/derived"])
EXPORT = KG_DIR / "vienna_kg.trig"

SPARQL_EXAMPLE = """
PREFIX vkg: <http://example.org/vienna-kg/>
SELECT ?name ?minutes WHERE {
  GRAPH <http://example.org/vienna-kg/graph/derived> {
    ?district vkg:offers <http://example.org/vienna-kg/pref/going_out> .
    ?journey vkg:from ?district ;
             vkg:to <http://example.org/vienna-kg/district/d01> ;
             vkg:minutes ?minutes .
  }
  GRAPH <http://example.org/vienna-kg/graph/ground> { ?district vkg:name ?name . }
  FILTER (?minutes <= 10)
}
ORDER BY ?minutes
"""


def _iri(kind: str, *parts: str) -> URIRef:
    return VKG[f"{kind}/" + "/".join(quote(str(part), safe="") for part in parts)]


def _district(district_id: str) -> URIRef:
    return _iri("district", district_id)


def _station(station_id: str) -> URIRef:
    return _iri("station", station_id)


def _venue(key: str) -> URIRef:
    return _iri("venue", key)


def build(knowledge: KnowledgeBase) -> Dataset:
    dataset = Dataset()
    dataset.bind("vkg", VKG)
    ground = dataset.graph(GROUND)
    derived = dataset.graph(DERIVED)
    _ground_facts(ground, knowledge)
    _derived_facts(derived, knowledge)
    return dataset


def _ground_facts(graph, knowledge: KnowledgeBase) -> None:
    for district in knowledge.districts.values():
        node = _district(district.id)
        graph.add((node, RDF.type, VKG.District))
        graph.add((node, VKG.name, Literal(district.name)))
        graph.add((node, VKG.number, Literal(district.number, datatype=XSD.integer)))
    for a, neighbours in knowledge.neighbours.items():
        for b in neighbours:
            graph.add((_district(a), VKG.adjacentTo, _district(b)))

    for i, row in enumerate(knowledge.observations.itertuples(index=False)):
        observation = VKG[f"observation/{i}"]
        graph.add((observation, RDF.type, VKG.Observation))
        graph.add((observation, VKG.district, _district(row.district)))
        graph.add((observation, VKG.indicator, VKG[f"indicator/{row.indicator}"]))
        graph.add((observation, VKG.value, Literal(float(row.value), datatype=XSD.double)))
        graph.add((observation, VKG.year, Literal(int(row.year), datatype=XSD.gYear)))
        graph.add((observation, VKG.source, VKG[f"source/{row.source}"]))

    pois = pd.read_csv(PROCESSED / "pois.csv")
    for row in pois.itertuples(index=False):
        venue = _venue(row.key)
        graph.add((venue, RDF.type, VKG[row.category]))
        graph.add((venue, VKG.locatedIn, _district(f"d{row.district:02d}")))
        graph.add((venue, VKG.source, VKG[f"source/{row.source}"]))
        if isinstance(row.name, str) and row.name:
            graph.add((venue, RDFS.label, Literal(row.name)))

    for station in knowledge.stations.values():
        node = _station(station.id)
        graph.add((node, RDF.type, VKG.Station))
        graph.add((node, VKG.name, Literal(station.name)))
        graph.add((node, VKG.locatedIn, _district(station.district)))
    for row in read_relation(schema.SEGMENT, KG_DIR).itertuples(index=False):
        segment = _iri("segment", row.from_station, row.to_station, row.line)
        graph.add((segment, RDF.type, VKG.Segment))
        graph.add((segment, VKG["from"], _station(row.from_station)))
        graph.add((segment, VKG.to, _station(row.to_station)))
        graph.add((segment, VKG.line, _iri("line", row.line)))
        graph.add((segment, VKG.minutes, Literal(int(row.minutes), datatype=XSD.integer)))


def _derived_facts(graph, knowledge: KnowledgeBase) -> None:
    subclasses = {
        "bar": "nightlife_venue",
        "pub": "nightlife_venue",
        "nightclub": "nightlife_venue",
        "biergarten": "nightlife_venue",
        "restaurant": "food_venue",
        "cafe": "food_venue",
        "market": "food_venue",
        "museum": "culture_venue",
        "kindergarten": "childcare",
        "childcare": "family_facility",
        "playground": "family_facility",
        "nightlife_venue": "leisure_venue",
        "food_venue": "leisure_venue",
        "culture_venue": "leisure_venue",
        "sport_venue": "leisure_venue",
    }
    for sub, sup in subclasses.items():
        graph.add((VKG[sub], RDFS.subClassOf, VKG[sup]))
    for preference in PREFERENCES:
        graph.add((VKG[f"pref/{preference.id}"], RDFS.label, Literal(preference.label)))

    for district, features in knowledge.features.items():
        for feature, value in features.items():
            assessment = VKG[f"assessment/{district}/{feature}"]
            graph.add((assessment, RDF.type, VKG.FeatureAssessment))
            graph.add((assessment, VKG.district, _district(district)))
            graph.add((assessment, VKG.feature, VKG[f"feature/{feature}"]))
            graph.add((assessment, VKG.value, Literal(float(value), datatype=XSD.double)))
            graph.add(
                (assessment, VKG.level, VKG[f"level/{knowledge.levels[(district, feature)]}"])
            )
            graph.add(
                (
                    assessment,
                    VKG.rank,
                    Literal(knowledge.ranks[(district, feature)], datatype=XSD.integer),
                )
            )
    for feature, label in FEATURE_LABELS.items():
        graph.add((VKG[f"feature/{feature}"], RDFS.label, Literal(label)))

    for district, preferences in knowledge.offers.items():
        for preference in preferences:
            graph.add((_district(district), VKG.offers, VKG[f"pref/{preference}"]))
    for district, hub in knowledge.hubs.items():
        graph.add((_district(district), VKG.hub, _station(hub.id)))
    for (a, b), minutes in knowledge.district_times.items():
        journey = VKG[f"journey/{a}/{b}"]
        graph.add((journey, RDF.type, VKG.Journey))
        graph.add((journey, VKG["from"], _district(a)))
        graph.add((journey, VKG.to, _district(b)))
        graph.add((journey, VKG.minutes, Literal(minutes, datatype=XSD.integer)))


def export(knowledge: KnowledgeBase) -> dict:
    dataset = build(knowledge)
    dataset.serialize(EXPORT, format="trig")
    rows = dataset.query(SPARQL_EXAMPLE)
    return {
        "file": EXPORT.relative_to(KG_DIR.parent.parent).as_posix(),
        "ground_triples": len(dataset.graph(GROUND)),
        "derived_triples": len(dataset.graph(DERIVED)),
        "sparql_example": SPARQL_EXAMPLE.strip(),
        "sparql_result": [(str(name), int(minutes)) for name, minutes in rows],
    }
