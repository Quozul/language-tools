from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from config import Settings
from tests.conftest import data_dir


@pytest.fixture(scope="module")
def client() -> TestClient:
    directory = data_dir()
    if directory is None:
        pytest.skip("data assets missing; run scripts/download_assets.py")
    settings = Settings(
        jmdict_furigana_csv=directory / "JmdictFurigana.json",
        max_text_length=50,
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


def test_health_becomes_ready(client: TestClient) -> None:
    body = client.get("/v1/health").json()
    assert body["ready"] is True


def test_capabilities_lists_japanese(client: TestClient) -> None:
    body = client.get("/v1/capabilities").json()
    assert "ja" in body["languages"]
    assert "hepburn-modified" in body["engines"]["ja"]["romanization_systems"]


def test_annotate_contract_fields(client: TestClient) -> None:
    response = client.post("/v1/annotate", json={"text": "東京", "language": "ja"})
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "ja"
    token = body["tokens"][0]
    assert token["surface"] == "東京"
    assert token["reading"] == "とうきょう"
    assert token["romaji"] == "tōkyō"
    assert [r["base"] for r in token["ruby"]] == ["東", "京"]
    assert token["confidence"] == "high"


def test_unsupported_language_is_explicit_error(client: TestClient) -> None:
    response = client.post("/v1/annotate", json={"text": "你好", "language": "zh"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsupported_language"


def test_too_long_input_rejected(client: TestClient) -> None:
    response = client.post("/v1/annotate", json={"text": "あ" * 51, "language": "ja"})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "input_too_long"


def test_options_are_echoed(client: TestClient) -> None:
    response = client.post(
        "/v1/annotate",
        json={"text": "東京", "language": "ja", "long_vowel_style": "plain"},
    )
    body = response.json()
    assert body["options_applied"]["long_vowel_style"] == "plain"
    assert body["tokens"][0]["romaji"] == "tokyo"


def test_compact_detail_returns_display_fields_only(client: TestClient) -> None:
    response = client.post(
        "/v1/annotate",
        json={"text": "東京", "language": "ja", "detail": "compact"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "language": "ja",
        "tokens": [
            {
                "surface": "東京",
                "romaji": "tōkyō",
                "ruby": [
                    {"base": "東", "text": "とう", "scope": "per-kanji"},
                    {"base": "京", "text": "きょう", "scope": "per-kanji"},
                ],
                "join_with_previous": False,
            }
        ],
    }
