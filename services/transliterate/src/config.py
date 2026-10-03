"""Configuration from environment variables only (docs 14.4)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    max_text_length: int = 5000
    data_dir: Path = Path("data")
    jmdict_furigana_csv: Path | None = None
    jmdict_furigana_names_csv: Path | None = None
    glossary_json: Path | None = None
    workers: int = 2
    cache_max_entries: int = 4096


@lru_cache
def get_settings() -> Settings:
    return Settings()
