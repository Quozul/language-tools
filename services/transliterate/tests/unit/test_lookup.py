from __future__ import annotations

import json
from pathlib import Path

from ja.lookup import parse_release_json


def write(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "entries.json"
    path.write_text("\ufeff" + json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return path


def test_parse_release_json_groups_readings(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        [
            {
                "text": "人気",
                "reading": "にんき",
                "furigana": [{"ruby": "人", "rt": "にん"}, {"ruby": "気", "rt": "き"}],
            },
            {
                "text": "人気",
                "reading": "ひとけ",
                "furigana": [{"ruby": "人", "rt": "ひと"}, {"ruby": "気", "rt": "け"}],
            },
        ],
    )
    entries = parse_release_json(path)
    assert len(entries) == 1
    entry = entries["人気"]
    assert [r.reading for r in entry.readings] == ["にんき", "ひとけ"]
    assert entry.readings[0].segments == (("人", "にん"), ("気", "き"))


def test_parse_release_json_plain_kana_segments(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        [
            {
                "text": "食べる",
                "reading": "たべる",
                "furigana": [{"ruby": "食", "rt": "た"}, {"ruby": "べる"}],
            },
        ],
    )
    entry = parse_release_json(path)["食べる"]
    assert entry.readings[0].segments == (("食", "た"), ("べる", ""))
