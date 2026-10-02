"""Stage 7: post-processing — word spacing (docs section 9.4).

Fixed policy, encoded here and in tests:
- Auxiliary verbs (補助動詞), auxiliary adjectives/verbs (助動詞) and
  bound morphemes/suffixes (接辞, incl. さん/ちゃん) join the previous token.
- Particles (助詞) stay separate words.
- Everything else starts a new word.
The decision travels to the client in ``join_with_previous``.
"""

from __future__ import annotations

from dataclasses import replace

from domain import Token

_JOIN_PREVIOUS_POS_PREFIXES = ("補助動詞", "助動詞", "接辞")
# Honorific suffixes are ordinary nouns in UniDic; the policy joins them.
_JOIN_PREVIOUS_SURFACES = frozenset({"さん", "ちゃん", "くん", "さま", "様"})


def _joins_previous(token: Token) -> bool:
    return (
        any(token.pos.startswith(p) for p in _JOIN_PREVIOUS_POS_PREFIXES)
        or token.surface in _JOIN_PREVIOUS_SURFACES
    )


def apply_word_spacing(tokens: list[Token]) -> list[Token]:
    result: list[Token] = []
    for index, token in enumerate(tokens):
        join = (
            index > 0 and token.romaji != "" and result[-1].romaji != "" and _joins_previous(token)
        )
        result.append(replace(token, join_with_previous=join))
    return result
