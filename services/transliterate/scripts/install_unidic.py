"""Install the UniDic dictionary into the unidic package directory.

Downloads the pinned zip from the self-hosted mirror (copyparty) first,
falling back to the upstream cotonoha S3 bucket, verifies the checksum,
then hands the local file to unidic's own installer logic (same layout as
`python -m unidic download`).

Usage:
    MIRROR_URL=https://files.quozul.dev/qzl-mirror python scripts/install_unidic.py
"""

from __future__ import annotations

import hashlib
import os
import sys
import urllib.request
from pathlib import Path

FILENAME = "unidic-3.1.0.zip"
VERSION = "3.1.0+2021-08-31"
SHA256 = "638718c4c63625ab300de4c92c67925d54c0e9e3830009eaa992f29819d59c43"
UPSTREAM_URL = "https://cotonoha-dic.s3-ap-northeast-1.amazonaws.com/unidic-3.1.0.zip"

MIRROR_BASE_URL = os.getenv("MIRROR_URL", "https://files.quozul.dev/qzl-mirror").rstrip("/")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    target = Path(os.getenv("UNIDIC_ZIP_CACHE", f"/tmp/{FILENAME}"))
    if target.exists() and sha256(target) != SHA256:
        print(f"{target}: bad cached copy, re-downloading")
        target.unlink()
    if not target.exists():
        for url in (f"{MIRROR_BASE_URL}/{FILENAME}", UPSTREAM_URL):
            print(f"unidic: downloading {url}")
            try:
                urllib.request.urlretrieve(url, target)
                break
            except OSError as exc:
                print(f"unidic: {url} failed ({exc}), trying next source", file=sys.stderr)
        else:
            print("unidic: all sources failed", file=sys.stderr)
            return 1
    actual = sha256(target)
    if actual != SHA256:
        print(f"unidic: CHECKSUM MISMATCH expected {SHA256} got {actual}", file=sys.stderr)
        target.unlink()
        return 1
    print("unidic: checksum verified")

    from unidic.download import download_and_clean

    # download_and_clean uses urlretrieve, which accepts file:// URLs.
    download_and_clean(VERSION, target.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
