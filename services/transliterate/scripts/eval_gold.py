"""Gold-set evaluation (docs section 11).

Usage: python scripts/eval_gold.py [gold.json]

Reports token reading accuracy, sentence exact match, ruby alignment
accuracy (per-kanji and group separately), and romaji exact match, sliced
per category. Unreviewed entries are counted and warned about (docs 11.1:
native review is the ground truth).
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Slice:
    tokens: int = 0
    reading_ok: int = 0
    romaji_ok: int = 0
    ruby_items: int = 0
    ruby_ok: int = 0
    sentences: int = 0
    sentence_ok: int = 0


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from config import Settings
    from domain import EngineOptions
    from ja import engine as ja_engine

    gold_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/gold/gold.json")
    entries = json.loads(gold_path.read_text(encoding="utf-8"))
    data_dir = Settings().data_dir
    settings = Settings(
        jmdict_furigana_csv=data_dir / "JmdictFurigana.json",
        jmdict_furigana_names_csv=data_dir / "JmnedictFurigana.json",
    )
    annotator = ja_engine.build(settings)
    options = EngineOptions(include_alternatives=False)

    slices: dict[str, Slice] = defaultdict(Slice)
    overall = Slice()
    unreviewed = 0

    for entry in entries:
        if not entry.get("reviewed", False):
            unreviewed += 1
        category = entry["category"]
        result = annotator.annotate(entry["text"], options)
        expected_tokens = entry["tokens"]
        actual = list(result.tokens)
        sentence_ok = len(actual) == len(expected_tokens)
        for exp in expected_tokens:
            index = expected_tokens.index(exp)
            if index >= len(actual):
                sentence_ok = False
                continue
            got = actual[index]
            for sl in (slices[category], overall):
                sl.tokens += 1
                if got.reading == exp["reading"]:
                    sl.reading_ok += 1
                if got.romaji == exp["romaji"]:
                    sl.romaji_ok += 1
                exp_ruby = [tuple(r) for r in exp["ruby"]]
                got_ruby = [(s.base, s.text, s.scope) for s in got.ruby]
                if exp_ruby or got_ruby:
                    sl.ruby_items += 1
                    if got_ruby == exp_ruby:
                        sl.ruby_ok += 1
            if got.reading != exp["reading"] or got.romaji != exp["romaji"]:
                sentence_ok = False
        for sl in (slices[category], overall):
            sl.sentences += 1
            sl.sentence_ok += int(sentence_ok)

    def report(name: str, s: Slice) -> None:
        pct = lambda a, b: f"{(100.0 * a / b) if b else 0.0:6.1f}%"  # noqa: E731
        print(
            f"{name:<24} tokens={s.tokens:<4} reading={pct(s.reading_ok, s.tokens)} "
            f"romaji={pct(s.romaji_ok, s.tokens)} ruby={pct(s.ruby_ok, s.ruby_items)} "
            f"sentence-exact={pct(s.sentence_ok, s.sentences)}"
        )

    for category in sorted(slices):
        report(category, slices[category])
    print("-" * 100)
    report("OVERALL", overall)
    if unreviewed:
        print(f"WARNING: {unreviewed} of {len(entries)} entries are not native-reviewed")
    failed = overall.reading_ok < overall.tokens or overall.romaji_ok < overall.tokens
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
