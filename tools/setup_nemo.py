"""Download and verify the Nemo rule engine binary for the current platform.

Usage: python tools/setup_nemo.py
The binary ends up in tools/nemo/<release-folder>/nmo(.exe). Not committed to git.
"""

import hashlib
import platform
import tarfile
import urllib.request
import zipfile
from pathlib import Path

VERSION = "v0.10.1"
BASE = f"https://github.com/knowsys/nemo/releases/download/{VERSION}"
TARGETS = {
    ("Windows", "AMD64"): "x86_64-pc-windows-msvc.zip",
    ("Linux", "x86_64"): "x86_64-unknown-linux-gnu.tar.gz",
    ("Linux", "aarch64"): "aarch64-unknown-linux-gnu.tar.gz",
    ("Darwin", "x86_64"): "x86_64-apple-darwin.tar.gz",
    ("Darwin", "arm64"): "aarch64-apple-darwin.tar.gz",
}
DEST = Path(__file__).parent / "nemo"


def main():
    target = TARGETS[(platform.system(), platform.machine())]
    asset = f"nemo_{VERSION}_{target}"
    DEST.mkdir(parents=True, exist_ok=True)
    archive = DEST / asset
    urllib.request.urlretrieve(f"{BASE}/{asset}", archive)
    expected = urllib.request.urlopen(f"{BASE}/{asset}.sha256sum").read().decode().split()[0]
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"Checksum mismatch: {actual} != {expected}")
    if asset.endswith(".zip"):
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(DEST)
    else:
        with tarfile.open(archive) as bundle:
            bundle.extractall(DEST)
    archive.unlink()
    print(f"Nemo {VERSION} installed to {DEST}")


if __name__ == "__main__":
    main()
