from pathlib import Path

import pandas as pd

from vdkg.config import KG_DIR
from vdkg.kg.schema import Relation


def write_relation(relation: Relation, frame: pd.DataFrame, directory: Path = KG_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{relation.name}.csv"
    frame[list(relation.columns)].to_csv(path, index=False, header=False)
    return path


def read_relation(relation: Relation, directory: Path = KG_DIR) -> pd.DataFrame:
    return pd.read_csv(directory / f"{relation.name}.csv", header=None, names=relation.columns)
