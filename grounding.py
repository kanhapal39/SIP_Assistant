"""Deterministic check for claims an answer makes that its source doc doesn't.

Used at answer time by llm.py (to retry / abstain) and by the eval (as a
regression signal). It's deliberately narrow: it flags the kinds of detail
models most often invent when "filling gaps" — directions, comparatives and
numbers — not paraphrase in general.
"""

import re
from typing import List

# Directional / comparative words that assert an outcome. Word families are
# matched by stem so "higher" and "high" are distinct, but "increase",
# "increases" and "increased" are one term.
_DIRECTION_TERMS = [
    "higher", "lower", "cheaper", "costlier", "greater", "fewer", "less", "more",
    "better", "worse", "increase", "decrease", "rise", "fall", "drop", "gain", "loss",
    "profit", "outperform", "underperform",
]
_DIRECTION_RE = re.compile(r"\b(" + "|".join(_DIRECTION_TERMS) + r")(s|d|ed|es|ing)?\b")
_NUMBER_RE = re.compile(r"\b\d+(\.\d+)?\s*%?")


def _norm(text: str) -> str:
    return text.lower().replace("‑", "-").replace("’", "'")


def unsupported_claims(answer: str, doc_text: str, question: str = "") -> List[str]:
    """Terms in `answer` that assert something `doc_text` doesn't contain.

    Direction words must appear in the doc itself — appearing only in the
    user's question isn't enough (that's exactly how "often higher" slipped
    in for B2). Numbers may also come from the question, so an answer can
    quote the user's claim in order to deny it ("no guaranteed 15%").
    """
    a, d, q = _norm(answer), _norm(doc_text), _norm(question)
    doc_directions = {m.group(1) for m in _DIRECTION_RE.finditer(d)}
    flagged = []
    for m in _DIRECTION_RE.finditer(a):
        if m.group(1) not in doc_directions and m.group(0) not in flagged:
            flagged.append(m.group(0))
    allowed_numbers = {n.group(0).replace(" ", "") for n in _NUMBER_RE.finditer(d + " " + q)}
    for n in _NUMBER_RE.finditer(a):
        num = n.group(0).replace(" ", "")
        if num not in allowed_numbers and num not in flagged:
            flagged.append(num)
    return flagged
