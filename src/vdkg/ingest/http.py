import hashlib
from pathlib import Path

import requests

from vdkg.config import RAW

USER_AGENT = "vienna-district-kg/0.1 (TU Wien Knowledge Graphs course project)"


def fetch(url: str, name: str | None = None, *, refresh: bool = False, timeout: int = 300) -> Path:
    """Download `url` once into data/raw and return the cached path."""
    RAW.mkdir(parents=True, exist_ok=True)
    target = RAW / (name or hashlib.sha1(url.encode()).hexdigest()[:16])
    if target.exists() and not refresh:
        return target
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    target.write_bytes(response.content)
    return target
