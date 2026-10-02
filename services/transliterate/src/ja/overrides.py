"""Stage 4: overrides / user glossary (docs section 4, stage 4).

A glossary maps a surface form to a forced hiragana reading. Corrections
applied here affect both furigana and romaji, because stage 6 consumes
this stage's output (docs section 4 design rule).
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from domain import Confidence, ReadingSource, Token


class OverrideStore:
    def __init__(self, readings: dict[str, str]) -> None:
        self._readings = readings

    @classmethod
    def from_json(cls, path: Path) -> OverrideStore:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls({str(k): str(v) for k, v in raw.items()})

    def apply(self, tokens: list[Token]) -> list[Token]:
        result: list[Token] = []
        for token in tokens:
            override = self._readings.get(token.surface)
            if override is None:
                result.append(token)
                continue
            result.append(
                replace(
                    token,
                    reading=override,
                    pronunciation=override,
                    source=ReadingSource.OVERRIDE,
                    confidence=Confidence.HIGH,
                    alternatives=(),
                )
            )
        return result
