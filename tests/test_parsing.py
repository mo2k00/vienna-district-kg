import math

import pytest

from vdkg.ingest.ma23 import district_number
from vdkg.ingest.numbers import parse_number
from vdkg.ingest.sports import sports_in
from vdkg.reasoning.nemo import parse_term


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1.571.123", 1571123.0),
        ("414,87", 414.87),
        (" 7.655.391 ", 7655391.0),
        ("4.965 m²", 4965.0),
        ("0,90%", 0.9),
    ],
)
def test_parse_number(text, expected):
    assert parse_number(text) == pytest.approx(expected)


def test_parse_number_empty():
    assert math.isnan(parse_number("")) and math.isnan(parse_number(None))


@pytest.mark.parametrize(
    ("code", "number"), [("90100", 1), ("92300", 23), ("90000", 0), ("90701", 7), ("9", 0)]
)
def test_district_number(code, number):
    assert district_number(code) == number


@pytest.mark.parametrize(
    ("text", "sports"),
    [
        ("Tennis", ["tennis"]),
        ("<br />Tischtennis", []),
        ("Sporthalle (Badminton, Basketball, Volleyball)", ["basketball", "volleyball"]),
        ("polysportiver Hartplatz", ["football", "basketball"]),
        ("Sommerbad", ["swimming"]),
        (None, []),
    ],
)
def test_sports_in(text, sports):
    assert sorted(sports_in(text)) == sorted(sports)


@pytest.mark.parametrize(
    ("term", "value"),
    [
        ('"d07"', "d07"),
        ("42", 42),
        ('"2.5"^^<http://www.w3.org/2001/XMLSchema#double>', 2.5),
        ("_:3", "_:3"),
    ],
)
def test_parse_term(term, value):
    assert parse_term(term) == value
