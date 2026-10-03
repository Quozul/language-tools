"""Shared fixtures. Dictionary/data-heavy fixtures skip cleanly unless
DATA_DIR points at downloaded assets (docs 11.4, 14.2)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from config import Settings
from ja import engine as ja_engine
from ja.analyzer import Analyzer


def data_dir() -> Path | None:
    raw = os.environ.get("DATA_DIR")
    if raw and Path(raw, "JmdictFurigana.json").exists():
        return Path(raw)
    default = Settings().data_dir
    if (default / "JmdictFurigana.json").exists():
        return default
    return None


@pytest.fixture(scope="session")
def analyzer() -> Analyzer:
    return Analyzer()


@pytest.fixture(scope="session")
def engine(analyzer: Analyzer):
    directory = data_dir()
    if directory is None:
        pytest.skip("data assets missing; run scripts/download_assets.py")
    settings = Settings(
        jmdict_furigana_csv=directory / "JmdictFurigana.json",
        jmdict_furigana_names_csv=directory / "JmnedictFurigana.json",
    )
    return ja_engine.build(settings)
