import json
from datetime import date

import pandas as pd
import requests

from vdkg.config import SNAPSHOTS
from vdkg.ingest.http import USER_AGENT
from vdkg.ingest.sources import OVERPASS_URL
from vdkg.ingest.sports import sports_in

SNAPSHOT = SNAPSHOTS / "osm_pois.json"

QUERY = """
[out:json][timeout:180];
area["name"="Wien"]["admin_level"="4"]->.vienna;
(
  nwr["amenity"~"^(bar|pub|nightclub|biergarten|restaurant|cafe|public_bath)$"](area.vienna);
  nwr["leisure"~"^(pitch|sports_centre|fitness_centre|fitness_station|water_park)$"](area.vienna);
  nwr["leisure"="swimming_pool"]["access"~"^(yes|public)$"](area.vienna);
);
out center tags;
"""

_AMENITIES = {"bar", "pub", "nightclub", "biergarten", "restaurant", "cafe", "public_bath"}
_SWIMMING_VENUES = {"public_bath", "water_park", "swimming_pool"}
_FITNESS_VENUES = {"fitness_centre", "fitness_station"}


def download_snapshot() -> None:
    response = requests.post(
        OVERPASS_URL, data={"data": QUERY}, headers={"User-Agent": USER_AGENT}, timeout=240
    )
    response.raise_for_status()
    payload = response.json()
    payload["snapshot_date"] = date.today().isoformat()
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _kind(tags: dict) -> str:
    amenity = tags.get("amenity")
    return amenity if amenity in _AMENITIES else tags.get("leisure", "")


def _category(tags: dict) -> str:
    value = _kind(tags)
    return "swimming_venue" if value in _SWIMMING_VENUES else value


def _sports(tags: dict) -> list[str]:
    value = _kind(tags)
    found = set(sports_in(tags.get("sport", "").replace(";", " ")))
    if value in _SWIMMING_VENUES:
        found.add("swimming")
    if value in _FITNESS_VENUES:
        found.add("fitness")
    return sorted(found)


def load_osm() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if not SNAPSHOT.exists():
        download_snapshot()
    payload = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    rows, sport_rows = [], []
    for element in payload["elements"]:
        tags = element.get("tags", {})
        position = element.get("center", element)
        key = f"osm:{element['type']}/{element['id']}"
        rows.append(
            {
                "key": key,
                "category": _category(tags),
                "name": tags.get("name", ""),
                "lon": position.get("lon"),
                "lat": position.get("lat"),
                "declared_district": float("nan"),
                "area_m2": float("nan"),
                "source": "osm",
            }
        )
        sport_rows.extend({"key": key, "sport": sport} for sport in _sports(tags))
    return pd.DataFrame(rows), pd.DataFrame(sport_rows), payload["snapshot_date"]
