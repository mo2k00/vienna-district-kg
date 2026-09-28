import numpy as np
import pandas as pd
from shapely import STRtree, points

METERS_PER_DEG_LAT = 111_320
METERS_PER_DEG_LON = 74_200
MATCH_RADIUS_M = 40.0


def _projected(pois: pd.DataFrame) -> np.ndarray:
    return points(pois["lon"] * METERS_PER_DEG_LON, pois["lat"] * METERS_PER_DEG_LAT)


def sport_venue_matches(pois: pd.DataFrame, sports: pd.DataFrame) -> pd.DataFrame:
    """Candidate pairs of records that likely describe the same sport venue.

    Blocking by sport, matching by distance. Deciding the final venues (transitive
    closure, canonical representative) is left to the rules.
    """
    located = pois.set_index("key")[["lon", "lat"]]
    pairs = []
    for sport, group in sports.groupby("sport"):
        venue = located.loc[group["key"].unique()].reset_index()
        geometry = _projected(venue)
        left, right = STRtree(geometry).query(
            geometry, predicate="dwithin", distance=MATCH_RADIUS_M
        )
        keep = left < right
        left, right = left[keep], right[keep]
        distance = np.hypot(
            (venue["lon"].to_numpy()[left] - venue["lon"].to_numpy()[right]) * METERS_PER_DEG_LON,
            (venue["lat"].to_numpy()[left] - venue["lat"].to_numpy()[right]) * METERS_PER_DEG_LAT,
        )
        pairs.append(
            pd.DataFrame(
                {
                    "key_a": venue["key"].to_numpy()[left],
                    "key_b": venue["key"].to_numpy()[right],
                    "sport": sport,
                    "distance_m": distance.round(1),
                }
            )
        )
    return pd.concat(pairs, ignore_index=True)
