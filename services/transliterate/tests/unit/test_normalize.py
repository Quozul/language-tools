from __future__ import annotations

from ja.normalize import normalize


def test_nfkc_folds_halfwidth_katakana() -> None:
    result, warnings = normalize("ｶﾀｶﾅ")
    assert result == "カタカナ"
    assert "half-width-katakana-normalized" in warnings


def test_nfkc_folds_fullwidth_latin_and_digits() -> None:
    result, _ = normalize("ＡＢＣ１２３")
    assert result == "ABC123"


def test_control_characters_stripped_and_warned() -> None:
    result, warnings = normalize("あ\x00\x07\x0bい")
    assert result == "あい"
    assert "control-characters-stripped" in warnings


def test_newline_preserved() -> None:
    result, warnings = normalize("あ\nい")
    assert result == "あ\nい"
    assert warnings == []
