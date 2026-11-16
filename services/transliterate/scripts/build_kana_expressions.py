"""Build the kana-expression asset for stage 2.5 (docs 14.5).

JmdictFurigana.json (our main lookup) only carries headwords that contain
kanji, so pure-kana JMdict vocabulary — ちなみに, とか, といけない, お世話に
なる … — is invisible to the expression merge even though UniDic splits
those surfaces into several morphemes. This script extracts the kana
headwords from a raw JMdict distribution file and keeps the ones worth
merging: JMdict ``expressions`` entries and priority-marked (common) ones.

Usage:
    python scripts/build_kana_expressions.py JMdict_e.xml[.gz] [dest]
    # dest default: data/JmdictKanaExpressions.json

Source file: JMdict_e from the EDRDG FTP
(http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz), CC BY-SA 4.0
(https://www.edrdg.org/edrdg/licence.html). Acknowledgement:
JMdict/EDICT project, https://www.edrdg.org/jmdict/edict.html
"""

from __future__ import annotations

import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Hiragana (+ chōon and iteration marks) only; katakana headwords resolve to
# their hiragana reading in the pipeline, so hiragana keys cover both.
HIRAGANA = re.compile("^[\u3041-\u3096\u30fc\u3005]+$")

MIN_LEN = 2
MAX_LEN = 8  # same window as the merge stage (_MAX_MERGE_PARTS chars are tiny)


def entries(path: Path):
    """Yield (reading, is_expression, has_priority_mark) per JMdict r_ele."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:
        for _, ent in ET.iterparse(fh):
            if ent.tag != "entry":
                continue
            is_expr = any(
                (pos.text or "").startswith("expressions")
                for sense in ent.findall("sense")
                for pos in sense.findall("pos")
            )
            has_pri = any(e.find("re_pri") is not None for e in ent.findall("r_ele")) or any(
                e.find("ke_pri") is not None for e in ent.findall("k_ele")
            )
            for r_ele in ent.findall("r_ele"):
                yield r_ele.findtext("reb") or "", is_expr, has_pri
            ent.clear()


def build(path: Path) -> dict:
    expr: dict[str, bool] = {}
    for reb, is_expression, has_priority in entries(path):
        if not (MIN_LEN <= len(reb) <= MAX_LEN) or not HIRAGANA.match(reb):
            continue
        if not (is_expression or has_priority):
            continue
        expr[reb] = expr.get(reb, False) or is_expression
    return {
        "source": "JMdict_e (EDRDG JMdict/EDICT project, CC BY-SA 4.0)",
        "guards": (
            "kana headwords (hiragana, len 2-8) that are JMdict expressions "
            "or carry a priority mark; the merge additionally guards "
            "all-particle runs by POS shape"
        ),
        "entries": [[surface, flag] for surface, flag in sorted(expr.items())],
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    src = Path(sys.argv[1])
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/JmdictKanaExpressions.json")
    payload = build(src)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"{dest}: {len(payload['entries'])} kana headwords")
    return 0


if __name__ == "__main__":
    sys.exit(main())
