"""Unknown kana words (e.g. a translation of "oogabooga") must still get romaji,
never the raw katakana surface."""

from __future__ import annotations

from domain import EngineOptions
from ja.analyzer import AnalyzerEntry
from ja.engine import JapaneseEngine
from ja.lookup import FuriganaLookup


class _StubAnalyzer:
    def __init__(self, entries: list[AnalyzerEntry]) -> None:
        self._entries = entries

    def analyze(self, text: str) -> list[AnalyzerEntry]:
        return list(self._entries)


def _engine(surface: str, reading: str, pronunciation: str, is_unknown: bool) -> JapaneseEngine:
    entry = AnalyzerEntry(
        surface=surface,
        pos="名詞,普通名詞,一般",
        reading=reading,
        pronunciation=pronunciation,
        lemma=surface,
        is_unknown=is_unknown,
    )
    return JapaneseEngine(
        analyzer=_StubAnalyzer([entry]),  # type: ignore[arg-type]
        lookup=FuriganaLookup(),
        overrides=None,
    )


def test_unknown_katakana_word_gets_romaji_not_surface() -> None:
    # UniDic reports the katakana reading, but the token is flagged unknown.
    engine = _engine("ウーガブーガ", "ウーガブーガ", "ウーガブーガ", is_unknown=True)
    (token,) = engine.annotate("ウーガブーガ", EngineOptions()).tokens
    assert token.romaji == "ūgabūga"


def test_unknown_katakana_word_without_features_gets_romaji() -> None:
    # OOV output can also carry no features at all ("*" readings).
    engine = _engine("ウーガブーガ", "", "", is_unknown=True)
    (token,) = engine.annotate("ウーガブーガ", EngineOptions()).tokens
    assert token.romaji == "ūgabūga"
