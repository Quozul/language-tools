"""Domain value objects. Immutable; shared by all engines (docs section 7.2/7.3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ReadingSource(StrEnum):
    ANALYZER = "analyzer"
    NAMES_DICTIONARY = "names-dictionary"
    OVERRIDE = "override"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RubyScope(StrEnum):
    PER_KANJI = "per-kanji"
    GROUP = "group"


class Flag(StrEnum):
    HETERONYM = "heteronym"
    PROPER_NOUN = "proper-noun"
    JUKUJIKUN = "jukujikun"
    UNKNOWN_WORD = "unknown-word"


@dataclass(frozen=True)
class RubySegment:
    base: str
    text: str
    scope: RubyScope


@dataclass(frozen=True)
class Alternative:
    reading: str
    source: str = "dictionary"


@dataclass(frozen=True)
class Token:
    surface: str
    pos: str
    reading: str | None
    pronunciation: str | None
    romaji: str = ""
    ruby: tuple[RubySegment, ...] = ()
    source: ReadingSource = ReadingSource.ANALYZER
    confidence: Confidence = Confidence.HIGH
    alternatives: tuple[Alternative, ...] = ()
    flags: frozenset[Flag] = frozenset()
    join_with_previous: bool = False
    lemma: str = ""


@dataclass(frozen=True)
class EngineOptions:
    romanization_system: str = "hepburn-modified"
    long_vowel_style: str = "macron"
    include_ruby: bool = True
    include_alternatives: bool = False
    word_spacing: bool = True


@dataclass(frozen=True)
class EngineResult:
    tokens: tuple[Token, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class EngineCapabilities:
    language: str
    engine: str
    romanization_systems: tuple[str, ...]
    option_defaults: dict[str, object] = field(default_factory=dict)
