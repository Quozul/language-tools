"""Stage 5: ruby alignment (docs section 9.7).

Preference order:
1. JmdictFurigana per-kanji ranges for the exact (surface, reading) pair.
2. Okurigana stripping; ruby on the remaining kanji run.
3. Group ruby for multi-kanji runs. Never guess a per-kanji split.
4. Whole-token group ruby with lowered confidence if nothing aligns.

Tokens that are entirely kana get no ruby.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from domain import Confidence, Flag, RubyScope, RubySegment, Token
from ja.lookup import EntryReading, FuriganaLookup


def is_kanji(ch: str) -> bool:
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF
        or 0x3400 <= code <= 0x4DBF
        or 0xF900 <= code <= 0xFAFF  # variant / compatibility ideographs
    )


def _has_kanji(text: str) -> bool:
    return any(is_kanji(c) for c in text)


def _segments_from_dictionary(reading: EntryReading) -> tuple[RubySegment, ...]:
    segments: list[RubySegment] = []
    for base, text in reading.segments:
        if not text or not _has_kanji(base):
            continue
        scope = RubyScope.GROUP if len(base) > 1 else RubyScope.PER_KANJI
        segments.append(RubySegment(base=base, text=text, scope=scope))
    return tuple(segments)


def _is_jukujikun(segments: Sequence[RubySegment]) -> bool:
    return any(s.scope is RubyScope.GROUP and len(s.base) > 1 for s in segments)


def align_ruby(tokens: list[Token], lookup: FuriganaLookup) -> list[Token]:
    result: list[Token] = []
    for token in tokens:
        if token.reading is None or not _has_kanji(token.surface):
            result.append(token)
            continue

        entry = lookup.lookup(token.surface) or lookup.lookup_name(token.surface)
        dict_reading = None
        if entry is not None:
            dict_reading = next((r for r in entry.readings if r.reading == token.reading), None)
        if dict_reading is not None:
            segments: list[RubySegment] = list(_segments_from_dictionary(dict_reading))
            if segments:
                flags = set(token.flags)
                if _is_jukujikun(segments):
                    flags.add(Flag.JUKUJIKUN)
                result.append(replace(token, ruby=tuple(segments), flags=frozenset(flags)))
                continue

        segments, jukujikun = _align_heuristic(token.surface, token.reading)
        flags = set(token.flags)
        confidence = token.confidence
        if jukujikun:
            flags.add(Flag.JUKUJIKUN)
            confidence = Confidence.MEDIUM  # group split guessed only by run length
        if not segments:
            base = token.surface if _has_kanji(token.surface) else ""
            if base:
                segments = [RubySegment(base=base, text=token.reading, scope=RubyScope.GROUP)]
                confidence = Confidence.MEDIUM
        result.append(
            replace(
                token,
                ruby=tuple(segments),
                flags=frozenset(flags),
                confidence=confidence,
            )
        )
    return result


def _align_heuristic(surface: str, reading: str) -> tuple[list[RubySegment], bool]:
    """Okurigana stripping, then per-kanji for a single kanji, else group."""
    okurigana_len = 0
    while okurigana_len < len(surface) and not is_kanji(surface[-okurigana_len - 1]):
        okurigana_len += 1
    stem = surface[: len(surface) - okurigana_len]
    stem_reading = reading
    if okurigana_len:
        suffix = surface[len(surface) - okurigana_len :]
        if not reading.endswith(suffix):
            return [], False
        stem_reading = reading[: len(reading) - okurigana_len]
    if not stem or not stem_reading:
        return [], False
    if all(is_kanji(c) for c in stem):
        if len(stem) == 1:
            return [RubySegment(base=stem, text=stem_reading, scope=RubyScope.PER_KANJI)], False
        return [RubySegment(base=stem, text=stem_reading, scope=RubyScope.GROUP)], True
    return [], False
