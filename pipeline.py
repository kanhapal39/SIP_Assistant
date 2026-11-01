"""The full question → response flow, shared by app.py and eval/run_eval.py.

Order matters:
  1. guardrails  — advice-seeking → fixed refusal, no LLM call.
  2. boundaries  — personal data / named fund → fixed abstention, no LLM call.
  3. retrieval   — nothing above threshold → fixed abstention, no LLM call.
  4. llm         — answers from the retrieved doc(s), or abstains itself.
"""

from dataclasses import dataclass
from typing import Optional

import boundaries
import guardrails
import llm
from retrieval import Retriever

# Response kinds, used by the UI for styling and by the eval for scoring.
REFUSE = "refuse"
ABSTAIN = "abstain"
ANSWER = "answer"


@dataclass
class Response:
    kind: str
    text: str
    stage: str  # which step decided: guardrails | boundaries | retrieval | llm
    rule: Optional[str] = None
    source_doc_id: Optional[str] = None
    source_title: Optional[str] = None
    top_score: Optional[float] = None
    attempts: int = 0  # LLM calls made (2 = the grounding check forced a retry)


def run(question: str, retriever: Retriever, client=None) -> Response:
    g = guardrails.check(question)
    if g.blocked:
        return Response(REFUSE, g.message, "guardrails", rule=g.rule)

    b = boundaries.check(question)
    if b.blocked:
        return Response(ABSTAIN, b.message, "boundaries", rule=f"{b.kind}/{b.rule}")

    top = retriever.search(question, k=1)
    top_score = top[0].score if top else 0.0
    hits = retriever.retrieve(question, k=2)
    if not hits:
        return Response(ABSTAIN, llm.ABSTENTION_MESSAGE, "retrieval", rule="below_threshold", top_score=top_score)

    a = llm.generate_answer(question, hits, client=client)
    if a.abstained:
        return Response(ABSTAIN, a.text, "llm", rule=f"llm_{a.abstain_reason}",
                        top_score=top_score, attempts=a.attempts)
    return Response(ANSWER, a.text, "llm", source_doc_id=a.source_doc_id,
                    source_title=a.source_title, top_score=top_score, attempts=a.attempts)
