import re

import pandas as pd

_NUMBER = re.compile(r"-?[\d.]+(?:,\d+)?")


def parse_number(text: str | float | None) -> float:
    """Parse Austrian-formatted numbers such as `1.571.123`, `414,87` or `4.965 m²`."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return float("nan")
    match = _NUMBER.search(str(text))
    if not match:
        return float("nan")
    return float(match.group().replace(".", "").replace(",", "."))
