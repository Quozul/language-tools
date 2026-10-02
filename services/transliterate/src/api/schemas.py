"""Request/response models mirroring the output contract (docs section 7)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from domain import Token


class AnnotateRequest(BaseModel):
    text: str
    language: str
    romanization_system: Literal["hepburn-modified", "kunrei-shiki", "nihon-shiki"] = (
        "hepburn-modified"
    )
    long_vowel_style: Literal["macron", "doubled", "ou", "plain"] = "macron"
    include_ruby: bool = True
    include_alternatives: bool = False
    word_spacing: bool = True
    detail: Literal["full", "compact"] = "full"


class RubySegmentModel(BaseModel):
    base: str
    text: str
    scope: str


class AlternativeModel(BaseModel):
    reading: str
    source: str


class TokenModel(BaseModel):
    surface: str
    pos: str
    reading: str | None
    romaji: str
    ruby: list[RubySegmentModel]
    source: str
    confidence: str
    alternatives: list[AlternativeModel]
    flags: list[str]
    join_with_previous: bool


class AnnotateResponse(BaseModel):
    language: str
    engine: str
    engine_version: str
    romanization_system: str
    options_applied: dict[str, object]
    tokens: list[TokenModel]
    warnings: list[str]


class CompactTokenModel(BaseModel):
    surface: str
    romaji: str
    ruby: list[RubySegmentModel]
    join_with_previous: bool


class CompactAnnotateResponse(BaseModel):
    language: str
    tokens: list[CompactTokenModel]


class CapabilitiesResponse(BaseModel):
    languages: list[str]
    engines: dict[str, dict[str, object]] = Field(default_factory=dict)


def to_token_model(token: Token) -> TokenModel:
    return TokenModel(
        surface=token.surface,
        pos=token.pos,
        reading=token.reading,
        romaji=token.romaji,
        ruby=[RubySegmentModel(base=s.base, text=s.text, scope=s.scope) for s in token.ruby],
        source=token.source,
        confidence=token.confidence,
        alternatives=[
            AlternativeModel(reading=a.reading, source=a.source) for a in token.alternatives
        ],
        flags=sorted(token.flags),
        join_with_previous=token.join_with_previous,
    )


def to_compact_token_model(token: Token) -> CompactTokenModel:
    return CompactTokenModel(
        surface=token.surface,
        romaji=token.romaji,
        ruby=[RubySegmentModel(base=s.base, text=s.text, scope=s.scope) for s in token.ruby],
        join_with_previous=token.join_with_previous,
    )
