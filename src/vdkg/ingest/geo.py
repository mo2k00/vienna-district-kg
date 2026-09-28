import json
from dataclasses import dataclass
from functools import cached_property

import numpy as np
import pandas as pd
from shapely import STRtree, points
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from vdkg.ingest.http import fetch
from vdkg.ingest.sources import DISTRICT_BORDERS_URL

BORDER_TOLERANCE_DEG = 1e-4
MIN_SHARED_BORDER_DEG = 1e-3


@dataclass(frozen=True)
class District:
    number: int
    name: str
    geometry: BaseGeometry


class DistrictMap:
    def __init__(self, geojson: dict):
        self.geojson = geojson
        self.districts = sorted(
            (
                District(
                    int(feature["properties"]["BEZNR"]),
                    feature["properties"]["NAMEK"],
                    shape(feature["geometry"]),
                )
                for feature in geojson["features"]
            ),
            key=lambda district: district.number,
        )

    @classmethod
    def load(cls) -> "DistrictMap":
        path = fetch(DISTRICT_BORDERS_URL, "district_borders.geojson")
        return cls(json.loads(path.read_text(encoding="utf-8")))

    @cached_property
    def _index(self) -> STRtree:
        return STRtree([district.geometry for district in self.districts])

    def locate(self, lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
        """District number for each coordinate, 0 if outside Vienna."""
        result = np.zeros(len(lon), dtype=int)
        point_idx, district_idx = self._index.query(points(lon, lat), predicate="within")
        numbers = np.array([district.number for district in self.districts])
        result[point_idx] = numbers[district_idx]
        return result

    def adjacency(self) -> pd.DataFrame:
        rows = []
        for i, a in enumerate(self.districts):
            for b in self.districts[i + 1 :]:
                shared = a.geometry.buffer(BORDER_TOLERANCE_DEG).intersection(b.geometry.boundary)
                if shared.length > MIN_SHARED_BORDER_DEG:
                    rows.append((a.number, b.number))
        return pd.DataFrame(rows, columns=["district_a", "district_b"])

    def table(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "district": [d.number for d in self.districts],
                "name": [d.name for d in self.districts],
                "centroid_lat": [d.geometry.centroid.y for d in self.districts],
                "centroid_lon": [d.geometry.centroid.x for d in self.districts],
            }
        )

    def web_geojson(self) -> dict:
        features = [
            {
                "type": "Feature",
                "properties": {"district": d.number, "name": d.name},
                "geometry": d.geometry.simplify(2e-5).__geo_interface__,
            }
            for d in self.districts
        ]
        return {"type": "FeatureCollection", "features": features}
