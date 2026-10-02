from __future__ import annotations

import pytest

from ja.romanize import romanize


@pytest.mark.parametrize(
    ("katakana", "expected"),
    [
        ("トーキョー", "tōkyō"),
        ("オーサカ", "ōsaka"),
        ("ビール", "bīru"),  # docs 9.5: katakana by Japanese pronunciation
        ("キョー", "kyō"),
        ("キッテ", "kitte"),  # sokuon
        ("キップ", "kippu"),  # n -> m before p
        ("アンバ", "amba"),  # n -> m before b
        ("ジュンイチ", "jun'ichi"),  # n before y
        ("シャ", "sha"),
        ("チャ", "cha"),
        ("チャット", "chatto"),  # sokuon before cha doubles t
        ("ッ", ""),
    ],
)
def test_hepburn_macron(katakana: str, expected: str) -> None:
    assert romanize(katakana) == expected


def test_long_vowel_styles() -> None:
    assert romanize("トーキョー", long_vowel_style="doubled") == "tookyoo"
    assert romanize("トーキョー", long_vowel_style="plain") == "tokyo"
    assert romanize("キョー", long_vowel_style="ou") == "kyou"
    assert romanize("セー", long_vowel_style="ou") == "see"


def test_systems() -> None:
    assert romanize("シ", system="hepburn-modified") == "shi"
    assert romanize("シ", system="kunrei-shiki") == "si"
    assert romanize("チ", system="kunrei-shiki") == "ti"
    assert romanize("フ", system="nihon-shiki") == "hu"
    assert romanize("ヅ", system="nihon-shiki") == "du"


def test_unknown_system_rejected() -> None:
    with pytest.raises(ValueError):
        romanize("ア", system="passport")
