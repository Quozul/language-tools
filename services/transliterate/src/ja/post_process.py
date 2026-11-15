"""Stage 7: post-processing — word spacing (docs section 9.4).

Fixed policy, encoded here and in tests:
- Auxiliary verbs (補助動詞), auxiliary adjectives/verbs (助動詞) and
  bound morphemes/suffixes (接辞, incl. さん/ちゃん) join the previous token.
- Particles (助詞) stay separate words.
- Everything else starts a new word.
The decision travels to the client in ``join_with_previous``.

Joining also propagates word-boundary gemination: UniDic places the っ of
forms like 降っ|た at a token boundary, so stage 6 romanizes フッ with no
following mora and drops it ("fu" + "ta" = "futa"). When a token joins and
the previous pronunciation ends in っ, the joined romaji's onset doubles,
mirroring romanize._assemble's sokuon rule → "futta".
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


def _propagate_gemination(token: Token, previous: Token) -> Token:
    """Double the joined token's romaji onset after a previous っ.

    Same sokuon rule as romanize._assemble: っ assimilates to the following
    stop, surfacing as t before ch/ts morae, else the onset letter. Vowel
    onsets take no gemination; the dropped っ stays dropped.
    """
    pron = previous.pronunciation
    if not pron or not pron.endswith(("ッ", "っ")):
        return token
    onset = token.romaji[:1]
    if not onset.isascii() or not onset.isalpha() or onset in "aeiou":
        return token
    gem = "t" if token.romaji[:2] in ("ch", "ts") else onset
    return replace(token, romaji=gem + token.romaji)


def apply_word_spacing(tokens: list[Token]) -> list[Token]:
    result: list[Token] = []
    for index, token in enumerate(tokens):
        join = (
            index > 0 and token.romaji != "" and result[-1].romaji != "" and _joins_previous(token)
        )
        joined = replace(token, join_with_previous=join)
        if join:
            joined = _propagate_gemination(joined, result[-1])
        result.append(joined)
    return result
