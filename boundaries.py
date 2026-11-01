"""Deterministic capability-boundary checks (not advice — see guardrails.py).

These catch questions the bot *can't* answer no matter how well retrieval
scores, because the answer isn't in the curated corpus by design:

- personal_data: the user wants their own account/transaction figures.
- named_fund:    the user asks a factual question about a specific named fund.
                 The glossary will happily match "expense ratio of <Fund>",
                 so a retrieval threshold alone can't catch this.
"""

import re
from dataclasses import dataclass
from typing import Optional

PERSONAL_DATA_MESSAGE = (
    "Sorry, I don't have access to your account — check your transaction history in the app for that."
)

NAMED_FUND_MESSAGE = (
    "Sorry, I can't look up specific fund details — check the fund's factsheet or "
    "Scheme Information Document for that."
)

_MONTHS = r"(jan(uary)?|feb(ruary)?|mar(ch)?|apr(il)?|may|june?|july?|aug(ust)?|sep(t(ember)?)?|oct(ober)?|nov(ember)?|dec(ember)?)"

_PERSONAL_RULES = [
    ("my_current_specific", re.compile(r"\bmy (current|specific|actual|exact|latest)\b")),
    ("date", re.compile(rf"\b\d{{1,2}}(st|nd|rd|th)?\s+(of\s+)?{_MONTHS}\b")),
    ("date", re.compile(rf"\b{_MONTHS}\s+\d{{1,2}}(st|nd|rd|th)?\b")),
    ("date", re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b")),
    ("my_portfolio", re.compile(r"\bmy (portfolio|holdings|folio|statement)\b")),
    # "my account" only when the user wants us to look into it — plain
    # mentions like "enough balance in my account" are general questions.
    ("my_account", re.compile(
        r"\b(check|look at|look into|see|open|access|show|view|pull up|read)\b.{0,15}\bmy (\w+ )?account\b"
        r"|\bmy (\w+ )?account('s)? (details|data|status|history|statement|value|summary)\b"
    )),
    ("this_transaction", re.compile(r"\b(this|that) (specific )?(transaction|payment|debit|order|purchase|redemption|instalment|installment)\b")),
]

# Fund houses commonly used in fund names. Lowercase match, so it also
# catches "parag parikh flexi cap" typed without capitals.
_FUND_HOUSES = [
    "aditya birla", "bandhan", "baroda bnp", "canara robeco", "dsp", "edelweiss",
    "franklin", "hsbc", "invesco", "jm financial", "lic mf", "mahindra manulife",
    "mirae", "motilal oswal", "navi", "nippon", "parag parikh", "pgim", "quant",
    "quantum", "sundaram", "tata", "uti", "whiteoak", "360 one", "bajaj finserv",
    "helios", "samco", "shriram", "trust mf",
]
_FUND_HOUSE_RE = re.compile(r"\b(" + "|".join(re.escape(h) for h in _FUND_HOUSES) + r")\b")

# These are also banks, and "my SBI mandate failed" is a mandate question,
# not a fund lookup — so only count them when fund words follow closely.
_BANK_FUND_HOUSES = ["hdfc", "icici", "sbi", "axis", "kotak", "union"]
_BANK_FUND_RE = re.compile(
    r"\b(" + "|".join(_BANK_FUND_HOUSES) + r")\b(\s+[\w&-]+){0,3}?\s+"
    r"(fund|funds|mf|mutual|amc|scheme|flexi|bluechip|elss|index|nifty|small|mid|large|multi|focused|value|tax)\b"
)

# "<Proper Name> ... Fund" in the original casing, excluding generic
# category words so "Mutual Fund" or "Index Fund" aren't treated as names.
_GENERIC_WORDS = {
    "mutual", "index", "equity", "debt", "liquid", "hybrid", "flexi", "cap",
    "large", "mid", "small", "multi", "elss", "gold", "international", "sectoral",
    "thematic", "balanced", "overnight", "money", "market", "the", "a", "an",
    "what", "is", "my", "this", "that", "which", "how", "does", "do", "why",
}
_PROPER_FUND_RE = re.compile(r"\b((?:[A-Z][\w&.'-]*\s+){1,6})(Fund|Scheme)\b")


@dataclass
class BoundaryResult:
    blocked: bool
    kind: Optional[str] = None  # "personal_data" | "named_fund"
    rule: Optional[str] = None
    message: Optional[str] = None


def _normalise(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip()


def _named_fund(original: str) -> Optional[str]:
    lowered = original.lower()
    if _FUND_HOUSE_RE.search(lowered) or _BANK_FUND_RE.search(lowered):
        return "fund_house"
    for m in _PROPER_FUND_RE.finditer(original):
        words = [w.lower() for w in m.group(1).split()]
        if any(w not in _GENERIC_WORDS for w in words):
            return "proper_fund_name"
    return None


def check(question: str) -> BoundaryResult:
    """Return blocked=True with a fixed message if the question is out of bounds."""
    original = _normalise(question)
    q = original.lower()
    for name, pattern in _PERSONAL_RULES:
        if pattern.search(q):
            return BoundaryResult(True, "personal_data", name, PERSONAL_DATA_MESSAGE)
    rule = _named_fund(original)
    if rule:
        return BoundaryResult(True, "named_fund", rule, NAMED_FUND_MESSAGE)
    return BoundaryResult(blocked=False)
