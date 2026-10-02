"""Export the app's OpenAPI document to stdout or a file (docs 02, section 5.1).

Runs without dictionaries or data assets: FastAPI builds the schema from the
route signatures alone; the lifespan (dictionary loading) never executes.

Usage:
    python scripts/export_openapi.py [output.json]
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    from main import app

    schema = app.openapi()
    text = json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
