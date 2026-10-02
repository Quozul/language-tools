"""The Japanese engine: wires the pipeline stages (docs sections 4, 5.1)."""

from __future__ import annotations

from dataclasses import replace

import jaconv

from config import Settings
from domain import EngineCapabilities, EngineOptions, EngineResult, Token
from ja.analyzer import Analyzer
from ja.lookup import FuriganaLookup
from ja.normalize import normalize
from ja.overrides import OverrideStore
from ja.post_process import apply_word_spacing
from ja.resolve_reading import resolve_readings
from ja.romanize import LONG_VOWEL_STYLES, SYSTEMS, particle_romaji, romanize
from ja.ruby import align_ruby

# Japanese punctuation to Latin equivalents (docs 9.6).
_PUNCTUATION: dict[str, str] = {
    "。": ".",
    "、": ",",
    "「": '"',
    "」": '"',
    "『": "'",
    "』": "'",
    "？": "?",
    "！": "!",
    "：": ":",
    "；": ";",
}

ENGINE_NAME = "ja-unidic"


class JapaneseEngine:
    def __init__(
        self,
        analyzer: Analyzer,
        lookup: FuriganaLookup,
        overrides: OverrideStore | None,
        cache_max_entries: int = 4096,
        dictionary_info: str = "unknown-dictionary",
    ) -> None:
        self._analyzer = analyzer
        self._lookup = lookup
        self._overrides = overrides
        self._cache_max = cache_max_entries
        self._cache: dict[tuple[str, EngineOptions], EngineResult] = {}
        self._dictionary_info = dictionary_info

    @property
    def language(self) -> str:
        return "ja"

    @property
    def engine_version(self) -> str:
        return f"0.1.0+{self._dictionary_info}"

    @property
    def capabilities(self) -> EngineCapabilities:
        return EngineCapabilities(
            language=self.language,
            engine=ENGINE_NAME,
            romanization_systems=SYSTEMS,
            option_defaults={
                "romanization_system": "hepburn-modified",
                "long_vowel_styles": list(LONG_VOWEL_STYLES),
                "include_ruby": True,
                "include_alternatives": False,
                "word_spacing": True,
            },
        )

    def annotate(self, text: str, options: EngineOptions) -> EngineResult:
        key = (text, options)
        cached = self._cache.get(key)
        if cached is not None:
            return self._project(cached, options)

        normalized, warnings = normalize(text)
        entries = self._analyzer.analyze(normalized)
        tokens = resolve_readings(entries, self._lookup)
        if self._overrides is not None:
            tokens = self._overrides.apply(tokens)
        tokens = align_ruby(tokens, self._lookup)
        tokens = [self._romanize_token(t, options) for t in tokens]
        if options.word_spacing:
            tokens = apply_word_spacing(tokens)
        result = EngineResult(tokens=tuple(tokens), warnings=tuple(warnings))
        if len(self._cache) >= self._cache_max:
            self._cache.clear()
        self._cache[key] = result
        return self._project(result, options)

    def _romanize_token(self, token: Token, options: EngineOptions) -> Token:
        if token.surface in _PUNCTUATION:
            romaji = _PUNCTUATION[token.surface]
        elif (
            token.pos.startswith("助詞")
            and (p := particle_romaji(jaconv.kata2hira(token.surface), options.romanization_system))
            is not None
        ):
            romaji = p
        elif token.pronunciation:
            romaji = romanize(
                token.pronunciation,
                system=options.romanization_system,
                long_vowel_style=options.long_vowel_style,
            )
        else:
            romaji = token.surface
        return replace(token, romaji=romaji)

    def _project(self, result: EngineResult, options: EngineOptions) -> EngineResult:
        if options.include_ruby and options.include_alternatives:
            return result
        tokens = tuple(
            Token(
                surface=t.surface,
                pos=t.pos,
                reading=t.reading,
                pronunciation=t.pronunciation,
                romaji=t.romaji,
                ruby=t.ruby if options.include_ruby else (),
                source=t.source,
                confidence=t.confidence,
                alternatives=t.alternatives if options.include_alternatives else (),
                flags=t.flags,
                join_with_previous=t.join_with_previous,
                lemma=t.lemma,
            )
            for t in result.tokens
        )
        return EngineResult(tokens=tokens, warnings=result.warnings)


def build(settings: Settings) -> JapaneseEngine:
    """Startup wiring: heavy loading happens here only (docs 14.4)."""
    analyzer = Analyzer()
    lookup = FuriganaLookup()
    if settings.jmdict_furigana_csv is not None:
        lookup.load_common(settings.jmdict_furigana_csv)
    if settings.jmdict_furigana_names_csv is not None:
        lookup.load_names(settings.jmdict_furigana_names_csv)
    overrides = OverrideStore.from_json(settings.glossary_json) if settings.glossary_json else None
    return JapaneseEngine(
        analyzer=analyzer,
        lookup=lookup,
        overrides=overrides,
        cache_max_entries=settings.cache_max_entries,
        dictionary_info=analyzer.dictionary_info,
    )
