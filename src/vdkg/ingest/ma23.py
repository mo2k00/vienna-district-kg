import io
from pathlib import Path

import pandas as pd

from vdkg.config import DISTRICT_COUNT
from vdkg.ingest.http import fetch
from vdkg.ingest.numbers import parse_number
from vdkg.ingest.sources import CAR_DENSITY_URL, STATISTICS, StatisticsSeries

OBSERVATION_COLUMNS = ["district", "indicator", "value", "year", "source"]


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Cannot decode {path}")


def district_number(code: str) -> int:
    code = str(code).strip()
    return int(code[1:3]) if len(code) >= 3 and code.startswith("9") else 0


def read_series_table(text: str, skip_title: bool) -> pd.DataFrame:
    lines = text.splitlines()[1:] if skip_title else text.splitlines()
    frame = pd.read_csv(io.StringIO("\n".join(lines)), sep=";", dtype=str)
    return frame.loc[:, ~frame.columns.str.startswith("Unnamed")]


def latest_complete_year(frame: pd.DataFrame, year_column: str) -> int:
    counts = frame.groupby(year_column)["district"].nunique()
    return int(counts[counts >= DISTRICT_COUNT].index.astype(int).max())


def load_series(series: StatisticsSeries) -> pd.DataFrame:
    frame = read_series_table(read_text(fetch(series.url, f"ma23_{series.key}.csv")), True)
    for column, value in series.row_filter.items():
        frame = frame[frame[column].str.strip() == value]
    frame = frame.assign(district=frame["DISTRICT_CODE"].map(district_number))
    frame = frame[frame["district"].between(1, DISTRICT_COUNT)]
    year = latest_complete_year(frame, "REF_YEAR")
    frame = frame[frame["REF_YEAR"].astype(int) == year]

    values = frame[list(series.columns)].map(parse_number)
    values["district"] = frame["district"]
    values = values.groupby("district").sum() if series.sum_over else values.set_index("district")

    long = values.rename(columns=series.columns).reset_index()
    long = long.melt(id_vars="district", var_name="indicator", value_name="value")
    return long.assign(year=year, source=series.key)


def load_car_density() -> pd.DataFrame:
    frame = read_series_table(read_text(fetch(CAR_DENSITY_URL, "ma20_car_density.csv")), False)
    frame = frame.assign(district=frame["DISTRICT_CODE"].map(district_number))
    frame = frame[frame["district"].between(1, DISTRICT_COUNT)]
    year = latest_complete_year(frame, "YEAR")
    frame = frame[frame["YEAR"].astype(int) == year]
    return pd.DataFrame(
        {
            "district": frame["district"],
            "indicator": "cars_per_1000",
            "value": frame["CARS_PER_1000_CAPITA"].map(parse_number),
            "year": year,
            "source": "car_density",
        }
    )


def load_observations() -> pd.DataFrame:
    frames = [load_series(series) for series in STATISTICS] + [load_car_density()]
    observations = pd.concat(frames, ignore_index=True)[OBSERVATION_COLUMNS]
    return observations.sort_values(["indicator", "district"]).reset_index(drop=True)
