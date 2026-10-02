"""Contract tests every registered engine must pass (docs 14.1 Liskov)."""

from __future__ import annotations

import pytest

from config import Settings
from domain import EngineOptions
from engine import EngineRegistry
from ja import engine as ja_engine


@pytest.fixture(scope="module")
def registry() -> EngineRegistry:
    settings = Settings(jmdict_furigana_csv=Settings().data_dir / "JmdictFurigana.json")
    reg = EngineRegistry()
    reg.register(ja_engine.build(settings))
    return reg


def test_every_engine_declares_capabilities(registry: EngineRegistry) -> None:
    for language in registry.languages():
        engine = registry.get(language)
        assert engine is not None
        caps = engine.capabilities
        assert caps.language == language
        assert caps.engine
        assert caps.romanization_systems


def test_annotated_text_produces_tokens(registry: EngineRegistry) -> None:
    engine = registry.get("ja")
    assert engine is not None
    result = engine.annotate("東京は大きいです。", EngineOptions())
    assert result.tokens
    surfaces = "".join(t.surface for t in result.tokens)
    assert surfaces == "東京は大きいです。"


def test_empty_text_returns_no_tokens(registry: EngineRegistry) -> None:
    engine = registry.get("ja")
    assert engine is not None
    assert engine.annotate("", EngineOptions()).tokens == ()


def test_optional_fields_are_omitted_not_repurposed(registry: EngineRegistry) -> None:
    engine = registry.get("ja")
    assert engine is not None
    result = engine.annotate("食べる。", EngineOptions(include_ruby=False))
    for token in result.tokens:
        if "。" in token.surface:
            assert token.reading is None
            assert token.romaji == "."
            assert token.ruby == ()
