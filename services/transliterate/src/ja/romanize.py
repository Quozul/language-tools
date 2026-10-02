"""Stage 6: romanization (docs sections 4, 9.1, 9.2, 9.5).

Converts the resolved *pronunciation* (never the raw surface) to romaji.
Hepburn-modified is the default; Kunrei-shiki and Nihon-shiki are the
compatibility systems. Long vowel marks come from the pronunciation
field's ー, so 東京 → tōkyō and ビール → bīru (docs 9.5).
"""

from __future__ import annotations

_HEPBURN: dict[str, str] = {
    "ア": "a",
    "イ": "i",
    "ウ": "u",
    "エ": "e",
    "オ": "o",
    "カ": "ka",
    "キ": "ki",
    "ク": "ku",
    "ケ": "ke",
    "コ": "ko",
    "サ": "sa",
    "シ": "shi",
    "ス": "su",
    "セ": "se",
    "ソ": "so",
    "タ": "ta",
    "チ": "chi",
    "ツ": "tsu",
    "テ": "te",
    "ト": "to",
    "ナ": "na",
    "ニ": "ni",
    "ヌ": "nu",
    "ネ": "ne",
    "ノ": "no",
    "ハ": "ha",
    "ヒ": "hi",
    "フ": "fu",
    "ヘ": "he",
    "ホ": "ho",
    "マ": "ma",
    "ミ": "mi",
    "ム": "mu",
    "メ": "me",
    "モ": "mo",
    "ヤ": "ya",
    "ユ": "yu",
    "ヨ": "yo",
    "ラ": "ra",
    "リ": "ri",
    "ル": "ru",
    "レ": "re",
    "ロ": "ro",
    "ワ": "wa",
    "ヰ": "wi",
    "ヱ": "we",
    "ヲ": "wo",
    "ン": "n",
    "ガ": "ga",
    "ギ": "gi",
    "グ": "gu",
    "ゲ": "ge",
    "ゴ": "go",
    "ザ": "za",
    "ジ": "ji",
    "ズ": "zu",
    "ゼ": "ze",
    "ゾ": "zo",
    "ダ": "da",
    "ヂ": "ji",
    "ヅ": "zu",
    "デ": "de",
    "ド": "do",
    "バ": "ba",
    "ビ": "bi",
    "ブ": "bu",
    "ベ": "be",
    "ボ": "bo",
    "パ": "pa",
    "ピ": "pi",
    "プ": "pu",
    "ペ": "pe",
    "ポ": "po",
    "ヴ": "vu",
}

_HEPBURN_COMBOS: dict[str, str] = {
    "キャ": "kya",
    "キュ": "kyu",
    "キョ": "kyo",
    "シャ": "sha",
    "シュ": "shu",
    "ショ": "sho",
    "チャ": "cha",
    "チュ": "chu",
    "チョ": "cho",
    "ニャ": "nya",
    "ニュ": "nyu",
    "ニョ": "nyo",
    "ヒャ": "hya",
    "ヒュ": "hyu",
    "ヒョ": "hyo",
    "ミャ": "mya",
    "ミュ": "myu",
    "ミョ": "myo",
    "リャ": "rya",
    "リュ": "ryu",
    "リョ": "ryo",
    "ギャ": "gya",
    "ギュ": "gyu",
    "ギョ": "gyo",
    "ジャ": "ja",
    "ジュ": "ju",
    "ジョ": "jo",
    "ヂャ": "ja",
    "ヂュ": "ju",
    "ヂョ": "jo",
    "ジァ": "ja",
    "ビャ": "bya",
    "ビュ": "byu",
    "ビョ": "byo",
    "ピャ": "pya",
    "ピュ": "pyu",
    "ピョ": "pyo",
    "イァ": "fa",
    "イィ": "fi",
    "イェ": "ye",
    "ウァ": "wa",
    "ウェ": "we",
    "ウォ": "wo",
    "ヴァ": "va",
    "ヴィ": "vi",
    "ヴェ": "ve",
    "ヴォ": "vo",
    "ファ": "fa",
    "フィ": "fi",
    "フェ": "fe",
    "フォ": "fo",
    "ティ": "ti",
    "ディ": "di",
    "シェ": "she",
}

# System overrides applied on top of Hepburn (docs 9.1).
_SYSTEM_OVERRIDES: dict[str, dict[str, str]] = {
    "hepburn-modified": {},
    "kunrei-shiki": {
        "シ": "si",
        "チ": "ti",
        "ツ": "tu",
        "フ": "hu",
        "ジ": "zi",
        "ヂ": "zi",
    },
    "nihon-shiki": {
        "シ": "si",
        "チ": "ti",
        "ツ": "tu",
        "フ": "hu",
        "ジ": "di",
        "ヂ": "di",
        "ズ": "du",
        "ヅ": "du",
    },
}

_SYSTEM_COMBOS: dict[str, dict[str, str]] = {
    "hepburn-modified": {},
    "kunrei-shiki": {
        "シャ": "sya",
        "シュ": "syu",
        "ショ": "syo",
        "チャ": "tya",
        "チュ": "tyu",
        "チョ": "tyo",
        "ジャ": "zya",
        "ジュ": "zyu",
        "ジョ": "zyo",
        "ヂ": "zi",
    },
    "nihon-shiki": {
        "シャ": "sya",
        "シュ": "syu",
        "ショ": "syo",
        "チャ": "tya",
        "チュ": "tyu",
        "チョ": "tyo",
        "ジャ": "dya",
        "ジュ": "dyu",
        "ジョ": "dyo",
    },
}

_VOWELS = {"a": "a", "i": "i", "u": "u", "e": "e", "o": "o"}
_MACRON = {"a": "ā", "i": "ī", "u": "ū", "e": "ē", "o": "ō"}

_PHONETIC_PARTICLES = {"は": "wa", "へ": "e", "を": "o"}
_ORTHOGRAPHIC_PARTICLES = {"は": "ha", "へ": "he", "を": "wo"}

LONG_VOWEL_STYLES = ("macron", "doubled", "ou", "plain")
SYSTEMS = ("hepburn-modified", "kunrei-shiki", "nihon-shiki")


def romanize(
    pronunciation: str, system: str = "hepburn-modified", long_vowel_style: str = "macron"
) -> str:
    if system not in SYSTEMS:
        raise ValueError(f"unknown romanization system: {system!r}")
    if long_vowel_style not in LONG_VOWEL_STYLES:
        raise ValueError(f"unknown long vowel style: {long_vowel_style!r}")

    table = {**_HEPBURN, **_SYSTEM_OVERRIDES[system]}
    combos = {**_HEPBURN_COMBOS, **_SYSTEM_COMBOS[system]}

    morae: list[str] = []
    i = 0
    while i < len(pronunciation):
        pair = pronunciation[i : i + 2]
        if pair in combos:
            morae.append(combos[pair])
            i += 2
            continue
        ch = pronunciation[i]
        if ch == "ー":
            morae.append("ː")
        elif ch == "ッ" or ch == "っ":
            morae.append("˘")
        elif ch in table:
            morae.append(table[ch])
        i += 1
    return _assemble(morae, long_vowel_style)


def _last_vowel(romaji: str) -> str | None:
    for ch in reversed(romaji):
        if ch in _VOWELS:
            return ch
    return None


def _assemble(morae: list[str], long_vowel_style: str) -> str:
    out: list[str] = []
    for index, mora in enumerate(morae):
        if mora == "ː":
            vowel = _last_vowel("".join(out))
            if vowel is None:
                continue
            if long_vowel_style == "macron":
                out[-1] = (
                    (out[-1][:-1] + _MACRON[vowel])
                    if out[-1].endswith(vowel)
                    else out[-1] + _MACRON[vowel]
                )
            elif long_vowel_style == "doubled":
                out.append(vowel)
            elif long_vowel_style == "ou":
                out.append("u" if vowel == "o" else vowel)
            continue
        if mora == "˘":
            nxt = next((m for m in morae[index + 1 :] if m not in ("ː", "˘")), None)
            if nxt and nxt[0].isalpha():
                # Geminates assimilate to the following stop: chi/tsu (and
                # combos like cha/cho, historically t-initial) double "t".
                gem = "t" if nxt[:2] in ("ch", "ts") else nxt[0]
                out.append(gem)
            continue
        if mora == "n":
            nxt = next((m for m in morae[index + 1 :] if m not in ("ː", "˘")), "")
            if nxt[:1] in ("b", "m", "p"):
                out.append("m")
            elif nxt[:1] in ("y", "a", "i", "u", "e", "o"):
                out.append("n'")
            else:
                out.append("n")
            continue
        out.append(mora)
    return "".join(out)


def particle_romaji(surface_hiragana: str, system: str) -> str | None:
    """Particle rules are driven by part-of-speech by the caller (docs 9.3)."""
    table = _ORTHOGRAPHIC_PARTICLES if system == "nihon-shiki" else _PHONETIC_PARTICLES
    return table.get(surface_hiragana)
