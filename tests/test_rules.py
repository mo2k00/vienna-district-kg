import pytest

from vdkg.config import RULES

try:
    from vdkg.reasoning.nemo import Nemo

    nemo = Nemo()
except FileNotFoundError:
    nemo = None

pytestmark = pytest.mark.skipif(nemo is None, reason="Nemo not installed")

TOY_NETWORK = """
district("d01"). district("d02").
areaKm2("d01", 2.0). areaKm2("d02", 4.0).
stationIn("a", "d01"). stationIn("b", "d01"). stationIn("c", "d02").
segment("a", "b", "U1", 2, 100). segment("b", "a", "U1", 2, 100).
segment("b", "c", "U2", 3, 50). segment("c", "b", "U2", 3, 50).
segment("a", "c", "13A", 20, 10).
servedBy("a", "U1", "subway"). servedBy("b", "U1", "subway"). servedBy("b", "U2", "subway").
@export hub :- csv{}.
@export travelTime :- csv{}.
@export subwayLines :- csv{}.
"""


def test_transit_recursion_uses_transfer_penalty(tmp_path):
    result = nemo.run([RULES / "40_transit.rls"], tmp_path, facts=TOY_NETWORK)
    hubs = dict(result["hub"])
    assert hubs["d01"] == "b"
    times = {(d, s): t for d, s, t in result["travelTime"]}
    assert times[("d01", "c")] == 3
    assert times[("d02", "a")] == 3 + 2 + 4
    assert dict(result["subwayLines"]) == {"d01": 2, "d02": 0}
