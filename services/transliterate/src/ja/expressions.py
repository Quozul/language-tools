"""Stage 2.5: merge lexicalized multi-morpheme expressions (docs section 4).

UniDic segments strictly at morpheme level and has no entry for lexicalized
expressions like かも知れない ("maybe, perhaps"): the tagger splits it into
か + も + 知れ + ない, which surfaces as three "words" (ない joins 知れ via
the spacing policy; particles never join). JMdict lists such expressions as
single vocabulary items, so this stage repairs the boundaries before
readings are resolved; downstream stages (lookup, ruby, romanize, spacing)
then treat the expression as the single word it is.

Three mechanisms, in order per token window:

1. A small curated pattern list, applied first. It covers expressions that
   the dictionaries below cannot supply (polite かも知れません is not a
   headword — dictionaries list the plain form) and keeps the headline
   cases working when the JMDict data assets are not loaded.
2. JmdictFurigana-driven merge. Where consecutive analyzer tokens
   concatenate to a headword, the run merges into one token. Guards:
   - every part must be analyzer-known with a non-empty reading;
   - the composed reading must match one of the headword's readings after
     the same conversion resolve_readings will apply, so merging can never
     fabricate a furigana/romaji the dictionary doesn't attest and ruby
     alignment still finds the dictionary entry;
   - longest match wins (お世話になる before お世話);
   - a window caps cost on long texts.
   Conservatism is intended: inflected phrase forms (headword なる vs text
   になります) fail the reading check and stay split.
3. Kana-expression merge (JmdictKanaExpressions asset). JmdictFurigana
   only carries headwords containing kanji, so pure-kana JMdict vocabulary
   — ちなみに, とか, といけない, おねがいします … — is invisible above even
   though UniDic splits those surfaces too (ちなみ|に, と|か, いけ|ない).
   The asset holds hiragana JMdict headwords that are marked expressions or
   carry a priority mark; the merged reading must equal the headword itself.
   Kana runs spell out other words far more often than kanji runs, so
   all-particle runs get an extra guard: they merge only when the headword
   is a JMdict expression and the run has the shape 助詞,格助詞 + 助詞,副助詞
   — grammaticalized combinations like とか/とやら. That keeps compositional
   particle sequences (にも, かも, かな, からこそ, とは…) apart, matching the
   word-spacing policy's rule that particles stay separate words. Pure
   auxiliary chains (まし|た → ました) are skipped too: spacing already
   joins them onto the stem, so merging would only split them off again.

Unrelated text is left untouched — notably 知れない without a preceding
か/も ("may not know"), which is not a JMDict headword and matches no
pattern.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import jaconv

from ja.analyzer import AnalyzerEntry
from ja.lookup import FuriganaLookup
from ja.resolve_reading import orthographic_hiragana

# POS for merged expressions; 固定表現 is UniDic's own "fixed expression"
# part of speech. Deliberately not 助詞/助動詞/接辞 so the word-spacing and
# particle-romaji stages treat the merge as an ordinary standalone word.
_MERGED_POS = "固定表現,*,*,*"

# Curated expressions as analyzer surface sequences (mechanism 1). Where a
# variant tokenizes differently between UniDic builds (e.g. ません vs
# ませ + ん), every split is listed.
_CURATED_PATTERNS: frozenset[tuple[str, ...]] = frozenset(
    {
        ("か", "も", "知れ", "ない"),
        ("か", "も", "しれ", "ない"),
        ("か", "も", "知れ", "ません"),
        ("か", "も", "しれ", "ません"),
        ("か", "も", "知れ", "ませ", "ん"),
        ("か", "も", "しれ", "ませ", "ん"),
        ("か", "も", "知れない"),
        ("か", "も", "しれない"),
    }
)

# Longest run considered for the dictionary merges, in tokens. Set phrases
# longer than this are rare and unbounded windows cost O(n²) lookups.
_MAX_MERGE_PARTS = 8

# UniDic POS prefixes for the all-particle run guard (mechanism 3).
_JOSHI = "助詞"
_KAKU_JOSHI = "助詞,格助詞"
_FUKU_JOSHI = "助詞,副助詞"
# Auxiliaries and suffixes join the previous word under the spacing policy,
# so a pure chain of them (まし|た, headword ました) is already one display
# word; merging it into a 固定表現 would split it off the verb stem instead.
_AUXILIARY_POS = ("補助動詞", "助動詞", "接辞")


class KanaExpressions:
    """Hiragana JMdict headwords the kanji-only lookup cannot contain.

    Asset built by scripts/build_kana_expressions.py from raw JMdict; each
    entry maps the headword to whether JMdict marks it an expression.
    """

    def __init__(self) -> None:
        self._expr: dict[str, bool] = {}
        self.loaded = False

    def load(self, path: Path) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        self._expr = {surface: bool(flag) for surface, flag in payload["entries"]}
        self.loaded = True

    def is_expression(self, hiragana_surface: str) -> bool | None:
        """True/False when known, None when the surface is not a headword."""
        return self._expr.get(hiragana_surface)


def _merge_entry(parts: list[AnalyzerEntry], surface: str) -> AnalyzerEntry:
    """Fold a run of analyzer entries into one fixed-expression entry."""
    reading = "".join(part.reading for part in parts)
    return replace(
        parts[0],
        surface=surface,
        pos=_MERGED_POS,
        reading=reading,
        pronunciation=reading,  # Same field feeds both (docs 5.4).
        lemma=surface,
    )


def _parts_mergable(parts: list[AnalyzerEntry]) -> bool:
    return all(not part.is_unknown and part.reading for part in parts)


def _display_reading(surface: str, reading: str) -> str:
    """The hiragana reading resolve_readings will derive for this surface."""
    if any(0x30A1 <= ord(c) <= 0x30FF for c in surface):
        return jaconv.kata2hira(reading)
    return orthographic_hiragana(reading)


def _particle_run_mergable(parts: list[AnalyzerEntry]) -> bool:
    """Only grammaticalized 格助詞+副助詞 pairs (とか) may merge, never
    compositional particle sequences (にも, からこそ, …)."""
    return (
        len(parts) == 2
        and parts[0].pos.startswith(_KAKU_JOSHI)
        and parts[1].pos.startswith(_FUKU_JOSHI)
    )


def _try_merge(
    entries: list[AnalyzerEntry],
    start: int,
    lookup: FuriganaLookup | None,
    kana: KanaExpressions | None,
) -> tuple[AnalyzerEntry, int] | None:
    """Merge the longest match starting at `start` (curated, then
    JmdictFurigana, then the kana-expression asset)."""
    window = min(_MAX_MERGE_PARTS, len(entries) - start)
    for width in range(window, 1, -1):
        parts = entries[start : start + width]
        surfaces = tuple(part.surface for part in parts)
        if surfaces in _CURATED_PATTERNS:
            if _parts_mergable(parts):
                return _merge_entry(parts, "".join(surfaces)), width
            continue
        # Require non-empty readings before any dictionary hit: partial
        # readings must never satisfy a reading check by omission.
        if not _parts_mergable(parts):
            continue
        surface = "".join(surfaces)
        reading = "".join(part.reading for part in parts)
        entry = lookup.lookup(surface) if lookup is not None else None
        if entry is not None:
            composed = _display_reading(surface, reading)
            if any(r.reading == composed for r in entry.readings):
                return _merge_entry(parts, surface), width
            continue
        if kana is None:
            continue
        # Kana headwords read as they are spelled; text may be katakana.
        key = jaconv.kata2hira(surface)
        is_expression = kana.is_expression(key)
        if is_expression is None:
            continue
        if all(part.pos.startswith(_JOSHI) for part in parts) and not (
            is_expression and _particle_run_mergable(parts)
        ):
            continue
        if all(part.pos.startswith(_AUXILIARY_POS) for part in parts):
            continue
        if _display_reading(surface, reading) != key:
            continue
        return _merge_entry(parts, surface), width
    return None


def merge_expressions(
    entries: list[AnalyzerEntry],
    lookup: FuriganaLookup | None = None,
    kana: KanaExpressions | None = None,
) -> list[AnalyzerEntry]:
    result: list[AnalyzerEntry] = []
    index = 0
    while index < len(entries):
        merged = _try_merge(entries, index, lookup, kana)
        if merged is None:
            result.append(entries[index])
            index += 1
        else:
            entry, width = merged
            result.append(entry)
            index += width
    return result
