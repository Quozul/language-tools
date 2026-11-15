"""Stage 2.5: merge lexicalized multi-morpheme expressions (docs section 4).

UniDic segments strictly at morpheme level and has no entry for lexicalized
expressions like かも知れない ("maybe, perhaps"): the tagger splits it into
か + も + 知れ + ない, which surfaces as three "words" (ない joins 知れ via
the spacing policy; particles never join). JMdict lists such expressions as
single vocabulary items, so this stage repairs the boundaries before
readings are resolved; downstream stages (lookup, ruby, romanize, spacing)
then treat the expression as the single word it is.

Two mechanisms, in order:

1. Dictionary-driven merge. Where consecutive analyzer tokens concatenate to
   a JmdictFurigana headword, the run merges into one token. Guards:
   - every part must be analyzer-known with a non-empty reading;
   - the composed reading must match one of the headword's readings after
     the same conversion resolve_readings will apply, so merging can never
     fabricate a furigana/romaji the dictionary doesn't attest and ruby
     alignment still finds the dictionary entry;
   - longest match wins (お世話になる before お世話);
   - a window caps cost on long texts.
   Conservatism is intended: inflected phrase forms (headword なる vs text
   になります) fail the reading check and stay split.
2. A small curated pattern list, applied first. It covers expressions that
   JmdictFurigana cannot supply (polite かも知れません is not a headword —
   dictionaries list the plain form) and keeps the headline cases working
   when the JMDict data assets are not loaded.

Unrelated text is left untouched — notably 知れない without a preceding
か/も ("may not know"), which is not a JMDict headword and matches no
pattern.
"""

from __future__ import annotations

from dataclasses import replace

import jaconv

from ja.analyzer import AnalyzerEntry
from ja.lookup import FuriganaLookup
from ja.resolve_reading import orthographic_hiragana

# POS for merged expressions; 固定表現 is UniDic's own "fixed expression"
# part of speech. Deliberately not 助詞/助動詞/接辞 so the word-spacing and
# particle-romaji stages treat the merge as an ordinary standalone word.
_MERGED_POS = "固定表現,*,*,*"

# Curated expressions as analyzer surface sequences (mechanism 2). Where a
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

# Longest run considered for the dictionary merge, in tokens. Set phrases
# longer than this are rare and unbounded windows cost O(n²) lookups.
_MAX_MERGE_PARTS = 8


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


def _try_merge(
    entries: list[AnalyzerEntry], start: int, lookup: FuriganaLookup | None
) -> tuple[AnalyzerEntry, int] | None:
    """Merge the longest match starting at `start` (curated, then dictionary)."""
    window = min(_MAX_MERGE_PARTS, len(entries) - start)
    for width in range(window, 1, -1):
        parts = entries[start : start + width]
        surfaces = tuple(part.surface for part in parts)
        if surfaces in _CURATED_PATTERNS:
            if _parts_mergable(parts):
                return _merge_entry(parts, "".join(surfaces)), width
            continue
        if lookup is None:
            continue
        # Require non-empty readings before the dictionary hit too: partial
        # readings must never satisfy the reading check by omission.
        if not _parts_mergable(parts):
            continue
        surface = "".join(surfaces)
        entry = lookup.lookup(surface)
        if entry is None:
            continue
        composed = _display_reading(surface, "".join(part.reading for part in parts))
        if any(reading.reading == composed for reading in entry.readings):
            return _merge_entry(parts, surface), width
    return None


def merge_expressions(
    entries: list[AnalyzerEntry], lookup: FuriganaLookup | None = None
) -> list[AnalyzerEntry]:
    result: list[AnalyzerEntry] = []
    index = 0
    while index < len(entries):
        merged = _try_merge(entries, index, lookup)
        if merged is None:
            result.append(entries[index])
            index += 1
        else:
            entry, width = merged
            result.append(entry)
            index += width
    return result
