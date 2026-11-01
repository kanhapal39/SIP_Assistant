"""Deterministic advice-refusal pre-filter.

Runs BEFORE retrieval or any LLM call. If a question is asking for investment
advice (what to do with money, which fund to pick, roleplay as an advisor),
we return a fixed refusal and never call the LLM.

This module is intentionally scoped to advice-refusal only. Capability
boundaries (personal account data, out-of-corpus questions) live elsewhere.
"""

import re
from dataclasses import dataclass
from typing import Optional

REFUSAL_MESSAGE = (
    "Sorry, that's outside what I can help with — I don't give investment advice or recommend "
    "funds. For that, please speak with a SEBI-registered advisor."
)

# Each rule: (name, compiled pattern). Patterns run against a normalised,
# lowercased question. Order doesn't matter — any match refuses.
_RULES = [
    # Roleplay / jailbreak framing — checked as its own family so it's
    # caught even when the advice request itself is soft ("what you'd do").
    ("roleplay", re.compile(
        r"\b(pretend|act|behave|role-?play|imagine)\b.{0,40}\b(you are|you're|as an?|as my|like an?|like my)\b"
        r".{0,40}\b(advisor|adviser|planner|expert|broker|wealth manager|fund manager)\b"
    )),
    ("roleplay", re.compile(r"\byou are (now )?(my|an?) (financial )?(advisor|adviser|planner)\b")),
    ("jailbreak", re.compile(
        r"\b(ignore|forget|disregard|bypass)\b.{0,30}\b(instructions|rules|guidelines|restrictions|prompt)\b"
    )),
    ("what_would_you_do", re.compile(
        r"\bwhat (would|will|should) you do\b|\bwhat you'?d do\b|\bif you were me\b|\bin my (place|shoes)\b"
    )),

    # Direct decision questions about the user's own money.
    ("should_i", re.compile(r"\bshould (i|we)\b")),
    ("ought_to", re.compile(r"\b(do|would) you (think|suggest|advise|recommend) (i|we)\b")),
    ("is_it_wise", re.compile(
        r"\bis it (wise|smart|better|good|a good idea|a bad idea|worth it|safe|okay|ok|sensible|advisable)\b"
        r".{0,20}\b(to )?(invest|buy|sell|start|stop|pause|switch|redeem|put|withdraw|continue|hold)"
    )),
    ("is_it_wise_bare", re.compile(r"\bis it (wise|advisable|a good idea|a bad idea)\b")),
    ("worth_investing", re.compile(r"\b(worth|good time to|right time to) (investing|invest|buying|buy|selling|sell)\b")),
    ("good_bad_time", re.compile(r"\b(good|bad|right|best) time to (invest|buy|sell|start|stop|redeem|exit)\b")),

    # Picking / ranking funds.
    ("which_fund", re.compile(
        r"\bwhich (mutual )?(fund|funds|sip|sips|scheme|schemes|amc|plan|option)\b"
        r".{0,40}\b(should|to|best|better|good|pick|choose|start|buy|invest|recommend)\b"
    )),
    ("which_better", re.compile(r"\bwhich (one )?is (better|best|safer|good)\b")),
    ("best_fund", re.compile(
        r"\b(best|top|good|safest|highest[- ]return(ing)?)\s+(\w+\s+){0,3}"
        r"(fund|funds|sip|sips|scheme|schemes|mutual funds?|investment|investments)\b"
        r"(?!.{0,10}\bhouse\b)"
    )),
    ("is_x_good", re.compile(
        r"\bis (this|that|my|the|[a-z0-9&]+(\s+[a-z0-9&]+){0,5}) (fund|scheme|sip)\b.{0,20}"
        r"\b(good|bad|safe|worth|right|better|underperforming|a good|a bad)\b"
    )),
    ("recommend", re.compile(r"\b(recommend|suggest|advise)\b.{0,40}\b(fund|funds|sip|scheme|invest|portfolio|stock|stocks)\b")),
    ("recommend_me", re.compile(r"\b(recommend|suggest)( me| us)\b")),
    ("where_to_invest", re.compile(r"\bwhere (should|do|can) (i|we) (invest|put)\b|\bwhere to invest\b")),
    ("how_much_to_invest", re.compile(r"\bhow much (should|do) (i|we) (invest|put|save|allocate)\b")),
    ("allocation_advice", re.compile(r"\bhow (should|do) (i|we) (allocate|split|diversify|divide)\b")),
]


@dataclass
class GuardrailResult:
    blocked: bool
    rule: Optional[str] = None
    message: Optional[str] = None


def _normalise(text: str) -> str:
    text = text.lower()
    # Curly quotes from phones/keyboards → straight, so "you’re" == "you're".
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def check(question: str) -> GuardrailResult:
    """Return blocked=True with the fixed refusal if the question seeks advice."""
    q = _normalise(question)
    for name, pattern in _RULES:
        if pattern.search(q):
            return GuardrailResult(blocked=True, rule=name, message=REFUSAL_MESSAGE)
    return GuardrailResult(blocked=False)
