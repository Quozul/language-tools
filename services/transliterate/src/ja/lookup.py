"""JmdictFurigana lookup (docs 5.1, 9.7).

Parses the JmdictFurigana release JSON (Doublevil/JmdictFurigana), whose
entries look like:

    {"text": "食べる", "reading": "たべる",
     "furigana": [{"ruby": "食", "rt": "た"}, {"ruby": "べる"}]}

Segments appear in surface order. A segment with `rt` carries ruby for the
kanji in `ruby`; a segment without `rt` (okurigana, jukujikun kana) is plain
text. Multi-kanji ruby bases (jukujikun) become ``group`` scope downstream.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EntryReading:
    reading: str
    # Ruby segments in surface order: (kanji/plain base, furigana or "" if plain).
    segments: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Entry:
    surface: str
    readings: tuple[EntryReading, ...]


def parse_release_json(path: Path) -> dict[str, Entry]:
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    grouped: dict[str, list[EntryReading]] = {}
    for row in rows:
        segments = tuple((seg["ruby"], seg.get("rt", "")) for seg in row["furigana"])
        readings = grouped.setdefault(row["text"], [])
        if not any(r.reading == row["reading"] for r in readings):
            readings.append(EntryReading(reading=row["reading"], segments=segments))
    return {
        surface: Entry(surface=surface, readings=tuple(readings))
        for surface, readings in grouped.items()
    }


class FuriganaLookup:
    def __init__(self) -> None:
        self._entries: dict[str, Entry] = {}
        self._names: dict[str, Entry] = {}
        self.loaded_common = False
        self.loaded_names = False

    def load_common(self, path: Path) -> None:
        self._entries = parse_release_json(path)
        self.loaded_common = True

    def load_names(self, path: Path) -> None:
        self._names = parse_release_json(path)
        self.loaded_names = True

    def lookup(self, surface: str) -> Entry | None:
        return self._entries.get(surface)

    def lookup_name(self, surface: str) -> Entry | None:
        return self._names.get(surface)

    def reading_count(self, surface: str) -> int:
        entry = self._entries.get(surface)
        return len(entry.readings) if entry else 0
