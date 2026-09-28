"""Capture screenshots of the running web app with headless Chrome.

Usage: start `vdkg serve`, then `python tools/screenshots.py [base-url]`.
Set CHROME to the browser executable if it is not in the default location.
"""

import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

CHROME = os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
OUTPUT = Path(__file__).resolve().parents[1] / "artifacts" / "report" / "screenshots"

CROPS = {"recommend": (60, 195, 1380, 1030)}

PAGES = {
    "recommend": (
        "#/recommend/going_out=3&sport_tennis=2&green_quiet=1&nearby=10"
        "&station=at%3A49%3A657&station_name=Karlsplatz&commute=25",
        (1440, 1700),
    ),
    "similar": ("#/similar/d07", (1440, 1250)),
    "district": ("#/district/d07", (1440, 2300)),
    "about": ("#/about", (1440, 1300)),
}


def main() -> None:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, (fragment, (width, height)) in PAGES.items():
        target = OUTPUT / f"{name}.png"
        subprocess.run(
            [
                CHROME,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--window-size={width},{height}",
                "--virtual-time-budget=10000",
                f"--screenshot={target}",
                base + fragment,
            ],
            check=True,
            capture_output=True,
        )
        if name in CROPS:
            with Image.open(target) as image:
                image.crop(CROPS[name]).save(OUTPUT / f"{name}_crop.png")
        print(f"{name}: {target}")


if __name__ == "__main__":
    main()
