from __future__ import annotations

from pathlib import Path

from domain import Confidence, ReadingSource, Token
from ja.overrides import OverrideStore
from ja.post_process import apply_word_spacing


def tok(surface: str, pos: str, romaji: str) -> Token:
    return Token(surface=surface, pos=pos, reading=None, pronunciation=None, romaji=romaji)


def test_auxiliaries_join_previous() -> None:
    tokens = [tok("食べ", "動詞,一般", "tabe"), tok("ます", "助動詞", "masu")]
    result = apply_word_spacing(tokens)
    assert result[1].join_with_previous is True
    assert result[0].join_with_previous is False


def test_particles_stay_separate() -> None:
    tokens = [tok("学校", "名詞,普通名詞,一般", "gakkou"), tok("に", "助詞,格助詞", "ni")]
    result = apply_word_spacing(tokens)
    assert result[1].join_with_previous is False


def test_suffixes_join_previous() -> None:
    tokens = [
        tok("田中", "名詞,固有名詞,人名,姓", "tanaka"),
        tok("さん", "名詞,接尾辞,人名等", "san"),
    ]
    result = apply_word_spacing(tokens)
    assert result[1].join_with_previous is True


def test_override_replaces_reading_and_marks_source() -> None:
    store = OverrideStore({"日下部": "くさかべ"})
    original = tok("日下部", "名詞,固有名詞", "ひかきた")
    result = OverrideStore.apply(store, [original])
    assert result[0].reading == "くさかべ"
    assert result[0].source is ReadingSource.OVERRIDE
    assert result[0].confidence is Confidence.HIGH


def test_override_from_json(tmp_path: Path) -> None:
    path = tmp_path / "glossary.json"
    path.write_text('{"東": "ひがし"}', encoding="utf-8")
    store = OverrideStore.from_json(path)
    assert store._readings == {"東": "ひがし"}
