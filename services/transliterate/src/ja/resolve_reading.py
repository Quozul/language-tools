"""Stage 3: resolve reading (docs section 4, 5.4).

The orthographic reading feeds furigana; the pronunciation feeds romaji
(stage 6 consumes these, never the raw text).
"""

from __future__ import annotations

import jaconv

from domain import Alternative, Confidence, Flag, ReadingSource, Token
from ja.analyzer import AnalyzerEntry
from ja.lookup import FuriganaLookup

_MORA_VOWEL = {
    "ア": "a",
    "イ": "i",
    "ウ": "u",
    "エ": "e",
    "オ": "o",
    "カ": "a",
    "キ": "i",
    "ク": "u",
    "ケ": "e",
    "コ": "o",
    "サ": "a",
    "シ": "i",
    "ス": "u",
    "セ": "e",
    "ソ": "o",
    "タ": "a",
    "チ": "i",
    "ツ": "u",
    "テ": "e",
    "ト": "o",
    "ナ": "a",
    "ニ": "i",
    "ヌ": "u",
    "ネ": "e",
    "ノ": "o",
    "ハ": "a",
    "ヒ": "i",
    "フ": "u",
    "ヘ": "e",
    "ホ": "o",
    "マ": "a",
    "ミ": "i",
    "ム": "u",
    "メ": "e",
    "モ": "o",
    "ヤ": "a",
    "ユ": "u",
    "ヨ": "o",
    "ラ": "a",
    "リ": "i",
    "ル": "u",
    "レ": "e",
    "ロ": "o",
    "ワ": "a",
    "ヰ": "i",
    "ヱ": "e",
    "ヲ": "o",
    "ガ": "a",
    "ギ": "i",
    "グ": "u",
    "ゲ": "e",
    "ゴ": "o",
    "ザ": "a",
    "ジ": "i",
    "ズ": "u",
    "ゼ": "e",
    "ゾ": "o",
    "ダ": "a",
    "ヂ": "i",
    "ヅ": "u",
    "デ": "e",
    "ド": "o",
    "バ": "a",
    "ビ": "i",
    "ブ": "u",
    "ベ": "e",
    "ボ": "o",
    "パ": "a",
    "ピ": "i",
    "プ": "u",
    "ペ": "e",
    "ポ": "o",
    "ヴ": "u",
}
_SMALL_Y = {"ャ": "ア", "ュ": "ウ", "ョ": "ウ"}
_SMALL_VOWEL = {"ァ": "a", "ィ": "i", "ゥ": "u", "ェ": "e", "ォ": "o"}
# Orthographic long-vowel spelling (docs 5.4). After a pure vowel mora the
# kana doubles (オオキイ); after a consonant mora o/e become う/い
# (トウキョウ).
_LONG_AFTER_CONSONANT = {"a": "ア", "i": "イ", "u": "ウ", "e": "イ", "o": "ウ"}


def _is_all_kana(text: str) -> bool:
    # Katakana block end (0x30FF) includes the long-vowel mark ー (0x30FC).
    return bool(text) and all(0x3041 <= ord(c) <= 0x30FF for c in text)


def _orthographic_hiragana(kana: str) -> str:
    """Kana spelling of the reading: expand the ー long-vowel mark (docs 5.4)."""
    out: list[str] = []
    for ch in kana:
        if ch == "ー" and out:
            top = out[-1]
            if top in _SMALL_Y:
                out.append(_SMALL_Y[top])
            elif top in _SMALL_VOWEL:
                out.append(_LONG_AFTER_CONSONANT[_SMALL_VOWEL[top]])
            elif top in "アイウエオ":
                out.append(top)
            elif top in _MORA_VOWEL:
                out.append(_LONG_AFTER_CONSONANT[_MORA_VOWEL[top]])
            else:
                out.append(ch)
        else:
            out.append(ch)
    return jaconv.kata2hira("".join(out))


def resolve_readings(entries: list[AnalyzerEntry], lookup: FuriganaLookup) -> list[Token]:
    tokens: list[Token] = []
    for entry in entries:
        reading = entry.reading if entry.reading and not entry.is_unknown else None
        pron = entry.pronunciation if entry.pronunciation and not entry.is_unknown else None
        flags: set[Flag] = set()
        confidence = Confidence.HIGH
        alternatives: tuple[Alternative, ...] = ()
        source = ReadingSource.ANALYZER

        if entry.is_unknown:
            flags.add(Flag.UNKNOWN_WORD)
            confidence = Confidence.LOW
            if _is_all_kana(entry.surface):
                # Kana reads as written: an OOV kana word's reading and
                # pronunciation are its surface, so romaji still gets built
                # (stage 6) instead of falling back to the raw surface.
                reading = entry.surface
                pron = jaconv.hira2kata(entry.surface)
            else:
                reading = None
                pron = None
        else:
            dict_entry = lookup.lookup(entry.surface)
            if dict_entry is not None and len(dict_entry.readings) > 1:
                flags.add(Flag.HETERONYM)
                hiragana = _orthographic_hiragana(reading or "")
                alternatives = tuple(
                    Alternative(reading=jaconv.kata2hira(r.reading))
                    for r in dict_entry.readings
                    if jaconv.kata2hira(r.reading) != hiragana
                )
            if lookup.lookup_name(entry.surface) is not None:
                flags.add(Flag.PROPER_NOUN)

        tokens.append(
            Token(
                surface=entry.surface,
                pos=entry.pos,
                reading=(
                    jaconv.kata2hira(reading)
                    if any(0x30A1 <= ord(c) <= 0x30FF for c in entry.surface)
                    else _orthographic_hiragana(reading)
                )
                if reading
                else None,
                pronunciation=pron,
                source=source,
                confidence=confidence,
                alternatives=alternatives,
                flags=frozenset(flags),
                lemma=entry.lemma,
            )
        )
    return tokens
