import os
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data"
RAW = DATA / "raw"
SNAPSHOTS = DATA / "snapshots"
PROCESSED = DATA / "processed"
KG_DIR = DATA / "kg"
ARTIFACTS = ROOT / "artifacts"
MATERIALIZED = ARTIFACTS / "materialized"
EMBEDDINGS = ARTIFACTS / "embeddings"
WEB = ROOT / "web"
RULES = Path(__file__).parent / "reasoning" / "rules"

GTFS_DIR = Path(os.environ.get("VDKG_GTFS_DIR", RAW / "gtfs"))

NEMO_VERSION = "v0.10.1"


def nemo_executable() -> Path:
    if env := os.environ.get("VDKG_NEMO"):
        return Path(env)
    exe = "nmo.exe" if platform.system() == "Windows" else "nmo"
    matches = sorted((ROOT / "tools" / "nemo").glob(f"nemo_{NEMO_VERSION}_*/{exe}"))
    if not matches:
        raise FileNotFoundError("Nemo not found. Run `python tools/setup_nemo.py` first.")
    return matches[0]


DISTRICT_COUNT = 23
