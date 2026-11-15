"""Stage 7: post-processing — word spacing (docs section 9.4).

Fixed policy, encoded here and in tests:
- Auxiliary verbs (補助動詞), auxiliary adjectives/verbs (助動詞) and
  bound morphemes/suffixes (接辞, incl. さん/ちゃん) join the previous token.
- Particles (助詞) stay separate words, except the conjunctive te/で
  (助詞,接続助詞, surface て/で) bound to a verb/adjective stem, which
  joins like an auxiliary (待って = matte, not "ma te").
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
# Conjunctive te/で (助詞,接続助詞) are inflectional particles bound to a
# verb/adjective stem (待っ|て, 暑く|て): they belong inside the word, like
# the auxiliaries above. The guard is narrow on purpose — other conjunctive
# particles (が, けれど, のに…) and the homographic case-particle で (水|で)
# and adverbial particle って (猫|って) are different subtypes and stay
# separate words.
_JOIN_PREVIOUS_CONJ_SURFACES = frozenset({"て", "で"})
_JOIN_PREVIOUS_STEM_POS_PREFIXES = ("動詞", "形容詞", "形容動詞", "形状詞")


def _joins_previous(token: Token, previous: Token | None = None) -> bool:
    if any(token.pos.startswith(p) for p in _JOIN_PREVIOUS_POS_PREFIXES):
        return True
    if token.surface in _JOIN_PREVIOUS_SURFACES:
        return True
    return (
        previous is not None
        and token.pos.startswith("助詞,接続助詞")
        and token.surface in _JOIN_PREVIOUS_CONJ_SURFACES
        and previous.pos.startswith(_JOIN_PREVIOUS_STEM_POS_PREFIXES)
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
            index > 0
            and token.romaji != ""
            and result[-1].romaji != ""
            and _joins_previous(token, result[-1])
        )
        joined = replace(token, join_with_previous=join)
        if join:
            joined = _propagate_gemination(joined, result[-1])
        result.append(joined)
    return result
