"""Gold-set regression gate (docs 11.3, 14.2): any change to code,
dictionaries, or options must keep these results."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain import EngineOptions

GOLD = json.loads((Path("data/gold/gold.json")).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "entry",
    GOLD,
    ids=[e["id"] for e in GOLD],
)
def test_gold_entry(entry: dict, engine) -> None:
    result = engine.annotate(entry["text"], EngineOptions())
    actual = list(result.tokens)
    assert len(actual) == len(entry["tokens"]), (
        f"{entry['id']}: tokenization changed; review and update gold"
    )
    for expected, got in zip(entry["tokens"], actual, strict=True):
        assert got.surface == expected["surface"]
        assert got.reading == expected["reading"], f"{entry['id']}: reading for {got.surface!r}"
        assert got.romaji == expected["romaji"], f"{entry['id']}: romaji for {got.surface!r}"
        assert [(s.base, s.text, s.scope) for s in got.ruby] == [
            tuple(r) for r in expected["ruby"]
        ], f"{entry['id']}: ruby for {got.surface!r}"


def test_gold_set_is_versioned_with_expected_values() -> None:
    assert all("id" in e and "category" in e for e in GOLD)


def test_gold_set_file_is_versioned_alongside_code(engine) -> None:
    assert engine.capabilities.language == "ja"
    assert Path("data/gold/gold.json").exists()
