"""Stage 1: normalization (docs section 4, stage 1).

Policy:
- NFKC: folds half-width katakana, full-width Latin/digits (docs 10).
- Strip control characters other than newline/tab; the API layer rejects
  invalid input before this point.
- neologdn is deliberately not adopted yet: docs 5.1 requires evaluating it
  against plain NFKC on the gold set first.
"""

from __future__ import annotations

import re
import unicodedata

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HALFWIDTH_KATAKANA_RE = re.compile("[\uff61-\uff9f]")


def normalize(text: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    cleaned = _CONTROL_RE.sub("", text)
    if cleaned != text:
        warnings.append("control-characters-stripped")
    result = unicodedata.normalize("NFKC", cleaned)
    if _HALFWIDTH_KATAKANA_RE.search(cleaned):
        warnings.append("half-width-katakana-normalized")
    return result, warnings
