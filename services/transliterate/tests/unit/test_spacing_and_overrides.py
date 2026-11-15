from __future__ import annotations

from pathlib import Path

from domain import Confidence, EngineOptions, ReadingSource, Token
from ja.analyzer import AnalyzerEntry
from ja.overrides import OverrideStore
from ja.post_process import _propagate_gemination, apply_word_spacing


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


# --- word-boundary gemination (降っ|た -> fu + tta) -------------------------


def ttoken(surface: str, pos: str, romaji: str, pronunciation: str | None) -> Token:
    return Token(surface=surface, pos=pos, reading=None, pronunciation=pronunciation, romaji=romaji)


def test_gemination_doubles_onset_of_joined_token() -> None:
    tokens = [
        ttoken("降っ", "動詞,一般", "fu", "フッ"),
        ttoken("た", "助動詞", "ta", "タ"),
    ]
    result = apply_word_spacing(tokens)
    assert result[0].romaji == "fu"
    assert result[1].romaji == "tta"
    assert result[1].join_with_previous is True


def test_gemination_uses_t_before_ch_and_ts() -> None:
    tokens = [
        ttoken("待っ", "動詞,一般", "ma", "マッ"),
        ttoken("ちゃ", "補助動詞", "cha", "チャ"),
    ]
    result = apply_word_spacing(tokens)
    assert result[1].romaji == "tcha"


def test_gemination_applies_to_any_consonant_onset() -> None:
    tokens = [
        ttoken("引っ", "名詞,普通名詞", "hi", "ヒッ"),
        ttoken("越し", "動詞,一般", "koshi", "コシ"),
    ]
    result = apply_word_spacing(tokens)
    # 動詞 does not join, so no gemination outside a word.
    assert result[1].join_with_previous is False
    assert result[1].romaji == "koshi"
    joined = apply_word_spacing([tokens[0], ttoken("ちゃ", "補助動詞", "koshi", "コシ")])
    assert joined[1].romaji == "kkoshi"


def test_gemination_skips_vowel_onset_and_missing_pronunciation() -> None:
    tokens = [
        ttoken("言っ", "動詞,一般", "i", "イッ"),
        ttoken("える", "動詞,非自立可能", "eru", "エル"),
    ]
    # Not joined anyway, but even forcing the helper path leaves vowels alone.
    assert _propagate_gemination(tokens[1], tokens[0]).romaji == "eru"
    no_pron = ttoken("言っ", "動詞,一般", "i", None)
    assert _propagate_gemination(tokens[1], no_pron).romaji == "eru"


def test_gemination_engine_end_to_end() -> None:
    from ja.engine import JapaneseEngine
    from ja.lookup import FuriganaLookup

    entries = [
        AnalyzerEntry("大雨", "名詞,普通名詞,一般", "オーアメ", "オーアメ", "大雨", False),
        AnalyzerEntry("が", "助詞,格助詞", "ガ", "ガ", "が", False),
        AnalyzerEntry("降っ", "動詞,一般", "フッ", "フッ", "降る", False),
        AnalyzerEntry("た", "助動詞", "タ", "タ", "た", False),
        AnalyzerEntry("。", "補助記号,句点", "", "", "。", False),
    ]

    class _Stub:
        def analyze(self, text: str) -> list[AnalyzerEntry]:
            return list(entries)

    engine = JapaneseEngine(
        analyzer=_Stub(),  # type: ignore[arg-type]
        lookup=FuriganaLookup(),
        overrides=None,
    )
    tokens = engine.annotate("大雨が降った。", EngineOptions()).tokens
    assert [t.romaji for t in tokens] == ["ōame", "ga", "fu", "tta", "."]
    words: list[str] = []
    for t in tokens:
        if t.join_with_previous and words:
            words[-1] += t.romaji
        else:
            words.append(t.romaji)
    assert words == ["ōame", "ga", "futta", "."]


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
