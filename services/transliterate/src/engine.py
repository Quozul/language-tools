"""Engine interface and registry (docs section 3, 14.1).

Engines are registered at startup; the API layer never branches on language
codes beyond registry lookup.
"""

from __future__ import annotations

from typing import Protocol

from domain import EngineCapabilities, EngineOptions, EngineResult


class Engine(Protocol):
    """Small interface: annotate and capabilities, nothing else (docs 14.1)."""

    @property
    def language(self) -> str: ...

    @property
    def capabilities(self) -> EngineCapabilities: ...

    @property
    def engine_version(self) -> str: ...

    def annotate(self, text: str, options: EngineOptions) -> EngineResult: ...


class EngineRegistry:
    def __init__(self) -> None:
        self._engines: dict[str, Engine] = {}

    def register(self, engine: Engine) -> None:
        key = engine.language
        if key in self._engines:
            raise ValueError(f"engine already registered for language {key!r}")
        self._engines[key] = engine

    def get(self, language: str) -> Engine | None:
        return self._engines.get(language)

    def languages(self) -> tuple[str, ...]:
        return tuple(self._engines)
