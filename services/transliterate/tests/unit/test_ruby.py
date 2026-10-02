from __future__ import annotations

from domain import Confidence, Flag, RubyScope, Token
from ja.lookup import Entry, EntryReading, FuriganaLookup
from ja.ruby import align_ruby


def token(surface: str, reading: str | None) -> Token:
    return Token(surface=surface, pos="名詞,普通名詞,一般", reading=reading, pronunciation=None)


def lookup_with(entries: dict[str, Entry]) -> FuriganaLookup:
    lookup = FuriganaLookup()
    lookup._entries = entries
    return lookup


def test_dictionary_alignment_per_kanji() -> None:
    entry = Entry(
        surface="東京",
        readings=(EntryReading("とうきょう", (("東", "とう"), ("京", "きょう"))),),
    )
    tokens = align_ruby([token("東京", "とうきょう")], lookup_with({"東京": entry}))
    ruby = tokens[0].ruby
    assert [(s.base, s.text, s.scope) for s in ruby] == [
        ("東", "とう", RubyScope.PER_KANJI),
        ("京", "きょう", RubyScope.PER_KANJI),
    ]


def test_jukujikun_dictionary_group_scope() -> None:
    entry = Entry(
        surface="今日",
        readings=(EntryReading("きょう", (("今日", "きょう"),)),),
    )
    tokens = align_ruby([token("今日", "きょう")], lookup_with({"今日": entry}))
    assert tokens[0].ruby[0].scope is RubyScope.GROUP
    assert Flag.JUKUJIKUN in tokens[0].flags


def test_okurigana_stripping_fallback() -> None:
    tokens = align_ruby([token("食べ", "たべ")], FuriganaLookup())
    assert [(s.base, s.text) for s in tokens[0].ruby] == [("食", "た")]


def test_never_guess_multi_kanji_split() -> None:
    tokens = align_ruby([token("学校", "がっこう")], FuriganaLookup())
    ruby = tokens[0].ruby
    assert len(ruby) == 1
    assert ruby[0].base == "学校"
    assert ruby[0].scope is RubyScope.GROUP
    assert tokens[0].confidence is not Confidence.HIGH


def test_kana_only_tokens_get_no_ruby() -> None:
    tokens = align_ruby([token("たべる", "たべる")], FuriganaLookup())
    assert tokens[0].ruby == ()


def test_no_reading_no_ruby() -> None:
    tokens = align_ruby([token("。", None)], FuriganaLookup())
    assert tokens[0].ruby == ()
