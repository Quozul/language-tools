"""Download pinned data assets and verify checksums (docs 14.5).

Run at image build time and for local setup:
    python scripts/download_assets.py [dest_dir]   # default: data/
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://github.com/Doublevil/JmdictFurigana/releases/download/2.3.1%2B2026-09-25"

ASSETS = {
    "JmdictFurigana.json": "2a8e206f0b171fa5acdce89e5f5798621b227175e5bfa2db6bd92fef63dd962e",
    "JmnedictFurigana.json": "ad210aaddf0115509723307d99d02429318e639222549e9bc452050b6ce88db7",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    dest.mkdir(parents=True, exist_ok=True)
    for name, expected in ASSETS.items():
        target = dest / name
        if target.exists() and sha256(target) == expected:
            print(f"{name}: already present and verified")
            continue
        url = f"{BASE_URL}/{name}"
        print(f"{name}: downloading {url}")
        urllib.request.urlretrieve(url, target)
        actual = sha256(target)
        if actual != expected:
            print(f"{name}: CHECKSUM MISMATCH expected {expected} got {actual}", file=sys.stderr)
            target.unlink()
            return 1
        print(f"{name}: checksum verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
