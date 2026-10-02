"""Stage 2: morphological analysis (docs section 4, 5.4).

The fugashi/UniDic output is converted to domain values here and nowhere
else: this is the anti-corruption layer for the analyzer (docs 14.3).
"""

from __future__ import annotations

import importlib.metadata
from dataclasses import dataclass

import fugashi

# Field indices in the UniDic feature list (docs 5.4). Exact names/indices
# vary between dictionary builds; _validate_fields fails startup on a mismatch.
# Field 9 (読み) is the per-token kana reading with phonetic ー long marks;
# it feeds both furigana (after ー-expansion) and romaji. Field 11 carries
# lemma-based pronunciation and is wrong for inflected stems (e.g. 書き -> カク).
FIELD_READING = 9
FIELD_LEMMA = 10

_KANA_RANGE = (0x3041, 0x30FF)


def _clean(feature: str | None) -> str:
    return "" if not feature or feature == "*" else feature


def _is_kana(text: str) -> bool:
    return bool(text) and all(_KANA_RANGE[0] <= ord(c) <= _KANA_RANGE[1] for c in text)


@dataclass(frozen=True)
class AnalyzerEntry:
    surface: str
    pos: str
    reading: str
    pronunciation: str
    lemma: str
    is_unknown: bool


class Analyzer:
    """Wraps a MeCab tagger. One instance per worker process (docs 11.4)."""

    def __init__(self, tagger: fugashi.Tagger | None = None) -> None:
        self._tagger = tagger if tagger is not None else fugashi.Tagger()
        self._validate_fields()

    @property
    def dictionary_info(self) -> str:
        try:
            version = importlib.metadata.version("unidic")
        except importlib.metadata.PackageNotFoundError:
            info = self._tagger.dictionary_info
            version = str(info[0]["version"]) if info else "unknown"
        return f"unidic-{version}"

    def _validate_fields(self) -> None:
        for token in self._tagger("食べる"):
            features = token.feature
            if len(features) <= FIELD_READING:
                raise RuntimeError(f"UniDic feature list too short: {features!r}")
            reading, pron = features[FIELD_READING], features[FIELD_READING]
            if not _is_kana(reading) or not _is_kana(pron):
                raise RuntimeError(
                    f"UniDic reading/pronunciation field check failed: "
                    f"reading={reading!r} pronunciation={pron!r}"
                )
            return
        raise RuntimeError("startup test text produced no tokens")

    def analyze(self, text: str) -> list[AnalyzerEntry]:
        entries: list[AnalyzerEntry] = []
        for token in self._tagger(text):
            features = token.feature
            entries.append(
                AnalyzerEntry(
                    surface=token.surface,
                    pos=token.pos,
                    reading=_clean(features[FIELD_READING]),
                    pronunciation=_clean(features[FIELD_READING]),
                    lemma=_clean(features[FIELD_LEMMA]),
                    is_unknown=token.is_unk,
                )
            )
        return entries
