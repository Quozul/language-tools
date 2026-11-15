"""Expression merging (stage 2.5): curated かも知れない patterns plus the
JmdictFurigana-driven merge, including its reading-consistency guard."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from domain import EngineOptions
from ja.analyzer import AnalyzerEntry
from ja.engine import JapaneseEngine
from ja.expressions import merge_expressions
from ja.lookup import FuriganaLookup


def entry(surface: str, reading: str, pos: str = "名詞,普通名詞,一般") -> AnalyzerEntry:
    return AnalyzerEntry(
        surface=surface,
        pos=pos,
        reading=reading,
        pronunciation=reading,
        lemma=surface,
        is_unknown=False,
    )


def jmdict_lookup(tmp_path: Path, rows: list[dict]) -> FuriganaLookup:
    path = tmp_path / "JmdictFurigana.json"
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    lookup = FuriganaLookup()
    lookup.load_common(path)
    return lookup


FIXTURE_ROWS = [
    {
        "text": "行けない",
        "reading": "いけない",
        "furigana": [{"ruby": "行", "rt": "い"}, {"ruby": "けない"}],
    },
    {
        "text": "何時も",
        "reading": "いつも",
        "furigana": [{"ruby": "何時", "rt": "いつ"}, {"ruby": "も"}],
    },
    {
        "text": "幾つ",
        "reading": "いくつ",
        "furigana": [{"ruby": "幾", "rt": "いく"}, {"ruby": "つ"}],
    },
    {
        "text": "幾つも",
        "reading": "いくつも",
        "furigana": [{"ruby": "幾", "rt": "いく"}, {"ruby": "つ"}, {"ruby": "も"}],
    },
    {
        "text": "大雨",
        "reading": "たいう",
        "furigana": [{"ruby": "大", "rt": "たい"}, {"ruby": "雨", "rt": "う"}],
    },
]


# --- mechanism 2: curated patterns (no dictionary needed) -----------------


def test_curated_kanji_variant_merges_without_dictionary() -> None:
    entries = [
        entry("か", "カ", "助詞,副助詞"),
        entry("も", "モ", "助詞,係助詞"),
        entry("知れ", "シレ", "動詞,一般"),
        entry("ない", "ナイ", "助動詞"),
    ]
    (merged,) = merge_expressions(entries)
    assert merged.surface == "かも知れない"
    assert merged.reading == "カモシレナイ"
    assert merged.pos.startswith("固定表現")


@pytest.mark.parametrize(
    "polite_parts",
    [
        [("知れ", "シレ"), ("ません", "マセン")],
        [("知れ", "シレ"), ("ませ", "マセ"), ("ん", "ン")],
    ],
    ids=["ません", "ませ+ん"],
)
def test_curated_polite_variant(polite_parts: list[tuple[str, str]], tmp_path: Path) -> None:
    # JmdictFurigana only lists the plain form, so the polite variants must
    # merge even with a dictionary loaded that lacks them.
    lookup = jmdict_lookup(tmp_path, FIXTURE_ROWS)
    entries = [entry("か", "カ"), entry("も", "モ")] + [
        entry(surface, reading) for surface, reading in polite_parts
    ]
    (merged,) = merge_expressions(entries, lookup)
    assert merged.surface == "か" + "も" + "知れません"
    assert merged.reading == "カモシレマセン"


# --- mechanism 1: JmdictFurigana-driven merge -----------------------------


def test_dictionary_merge_attested_expression(tmp_path: Path) -> None:
    lookup = jmdict_lookup(tmp_path, FIXTURE_ROWS)
    entries = [entry("行け", "イケ", "動詞,一般"), entry("ない", "ナイ", "助動詞")]
    (merged,) = merge_expressions(entries, lookup)
    assert merged.surface == "行けない"
    assert merged.reading == "イケナイ"


def test_dictionary_merge_particle_run(tmp_path: Path) -> None:
    lookup = jmdict_lookup(tmp_path, FIXTURE_ROWS)
    entries = [entry("何時", "イツ", "名詞,代名詞"), entry("も", "モ", "助詞,係助詞")]
    (merged,) = merge_expressions(entries, lookup)
    assert merged.surface == "何時も"
    assert merged.reading == "イツモ"


def test_reading_mismatch_blocks_dictionary_merge(tmp_path: Path) -> None:
    # 大雨 is attested as たいう; the analyzer's オオ+アメ must not merge onto it.
    lookup = jmdict_lookup(tmp_path, FIXTURE_ROWS)
    entries = [entry("大", "オオ"), entry("雨", "アメ")]
    assert merge_expressions(entries, lookup) == entries


def test_longest_match_wins(tmp_path: Path) -> None:
    lookup = jmdict_lookup(tmp_path, FIXTURE_ROWS)
    entries = [
        entry("幾", "イク"),
        entry("つ", "ツ", "名詞,助数詞,一般"),
        entry("も", "モ", "助詞,係助詞"),
    ]
    (merged,) = merge_expressions(entries, lookup)
    assert merged.surface == "幾つも"


def test_bare_shirenai_not_merged(tmp_path: Path) -> None:
    # Without the preceding か/も the potential-negative reading is literal
    # ("may not know"), and 知れない is not a headword: stays as analyzed.
    lookup = jmdict_lookup(tmp_path, FIXTURE_ROWS)
    entries = [entry("知れ", "シレ", "動詞,一般"), entry("ない", "ナイ", "助動詞")]
    assert merge_expressions(entries, lookup) == entries


def test_unknown_parts_block_merge() -> None:
    parts = [
        AnalyzerEntry("か", "助詞", "カ", "カ", "か", False),
        AnalyzerEntry("も", "助詞", "モ", "モ", "も", False),
        AnalyzerEntry("知れ", "動詞", "シレ", "シレ", "知れる", True),
        entry("ない", "ナイ", "助動詞"),
    ]
    result = merge_expressions(parts)
    assert [e.surface for e in result] == ["か", "も", "知れ", "ない"]


def test_surrounding_tokens_kept_and_order_preserved() -> None:
    entries = [
        entry("彼", "カレ", "代名詞"),
        entry("の", "ノ", "助詞,準体助詞"),
        entry("か", "カ", "助詞,副助詞"),
        entry("も", "モ", "助詞,係助詞"),
        entry("知れ", "シレ", "動詞,一般"),
        entry("ない", "ナイ", "助動詞"),
    ]
    result = merge_expressions(entries)
    assert [e.surface for e in result] == ["彼", "の", "かも知れない"]


# --- engine-level ----------------------------------------------------------


class _StubAnalyzer:
    def __init__(self, entries: list[AnalyzerEntry]) -> None:
        self._entries = entries

    def analyze(self, text: str) -> list[AnalyzerEntry]:
        return list(self._entries)


def _real_jmdict() -> FuriganaLookup:
    lookup = FuriganaLookup()
    path = Path(os.environ.get("DATA_DIR", "data"), "JmdictFurigana.json")
    if not path.exists():
        path = Path("data", "JmdictFurigana.json")
    if path.exists():
        lookup.load_common(path)
    return lookup


_STUB_ENTRIES = [
    entry("猫", "ネコ", "名詞,普通名詞,一般"),
    entry("か", "カ", "助詞,副助詞"),
    entry("も", "モ", "助詞,係助詞"),
    entry("知れ", "シレ", "動詞,一般"),
    entry("ない", "ナイ", "助動詞"),
]


def test_engine_end_to_end_kamoshirenai_one_word() -> None:
    engine = JapaneseEngine(
        analyzer=_StubAnalyzer(_STUB_ENTRIES),  # type: ignore[arg-type]
        lookup=_real_jmdict(),
        overrides=None,
    )
    tokens = engine.annotate("猫かも知れない。", EngineOptions()).tokens
    assert [t.surface for t in tokens] == ["猫", "かも知れない"]
    expression = tokens[1]
    assert expression.reading == "かもしれない"
    assert expression.romaji == "kamoshirenai"
    assert expression.join_with_previous is False
    if expression.ruby:  # JmdictFurigana data present: dictionary ruby 知→し.
        assert ("知", "し") in [(s.base, s.text) for s in expression.ruby]


def test_engine_curated_merge_survives_missing_dictionary() -> None:
    engine = JapaneseEngine(
        analyzer=_StubAnalyzer(_STUB_ENTRIES),  # type: ignore[arg-type]
        lookup=FuriganaLookup(),
        overrides=None,
    )
    tokens = engine.annotate("猫かも知れない。", EngineOptions()).tokens
    assert [t.surface for t in tokens] == ["猫", "かも知れない"]
    assert tokens[1].romaji == "kamoshirenai"
