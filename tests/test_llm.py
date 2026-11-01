"""Offline tests for llm.py using a fake Groq client (no network, no key)."""

import json
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import llm  # noqa: E402
import retrieval  # noqa: E402

RETRIEVER = retrieval.Retriever()


class FakeClient:
    """Returns `content` (or each item of a list, in turn) as the model reply."""

    def __init__(self, content):
        self.replies = list(content) if isinstance(content, list) else None
        self.content = content
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        msg = SimpleNamespace(content=self.replies.pop(0) if self.replies is not None else self.content)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def _hits(q="What is exit load?"):
    return RETRIEVER.retrieve(q)


def test_no_hits_abstains_without_calling_llm():
    client = FakeClient("{}")
    a = llm.generate_answer("What's the weather?", [], client=client)
    assert a.abstained and a.text == llm.ABSTENTION_MESSAGE
    assert client.calls == []


def test_valid_answer_carries_source_title():
    client = FakeClient(json.dumps({"abstain": False, "answer": "A fee on early redemption.",
                                    "source_doc_id": "glossary/exit_load.md"}))
    a = llm.generate_answer("What is exit load?", _hits(), client=client)
    assert not a.abstained
    assert a.source_title == "Exit Load"
    call = client.calls[0]
    assert call["model"] == "openai/gpt-oss-120b" and call["temperature"] == 0.0
    assert 'doc_id="glossary/exit_load.md"' in call["messages"][1]["content"]


@pytest.mark.parametrize("content", [
    json.dumps({"abstain": True, "answer": "", "source_doc_id": ""}),
    json.dumps({"abstain": False, "answer": "Something", "source_doc_id": "glossary/nav.md"}),  # not supplied
    json.dumps({"abstain": False, "answer": "", "source_doc_id": "glossary/exit_load.md"}),
    "not json at all",
])
def test_bad_or_abstaining_output_falls_back_to_abstention(content):
    a = llm.generate_answer("What is exit load?", _hits(), client=FakeClient(content))
    assert a.abstained and a.text == llm.ABSTENTION_MESSAGE


@pytest.mark.parametrize("flag,model_text", [
    (True, "A delay can shift which day's NAV applies."),
    (True, "I can't confirm what happened in your transaction. A delay can shift which day's NAV applies."),
])
def test_user_event_gets_exactly_one_cant_confirm_prefix(flag, model_text):
    content = json.dumps({"abstain": False, "about_user_event": flag, "answer": model_text,
                          "source_doc_id": "glossary/exit_load.md"})
    a = llm.generate_answer("What is exit load?", _hits(), client=FakeClient(content))
    assert a.text.startswith(llm.CANT_CONFIRM_MESSAGE)
    assert a.text.lower().count("can't confirm") == 1


def test_general_question_gets_no_prefix():
    content = json.dumps({"abstain": False, "about_user_event": False, "answer": "A fee.",
                          "source_doc_id": "glossary/exit_load.md"})
    a = llm.generate_answer("What is exit load?", _hits(), client=FakeClient(content))
    assert a.text == "A fee."


def _reply(answer, doc="faq/nav_allocation_timing.md"):
    return json.dumps({"abstain": False, "about_user_event": False, "answer": answer, "source_doc_id": doc})


NAV_Q = "I bought at one NAV but got a different, higher NAV value — why?"


def test_ungrounded_direction_is_retried_then_accepted():
    client = FakeClient([_reply("A later day's NAV may apply, which could be higher."),
                         _reply("A later day's NAV may apply.")])
    a = llm.generate_answer(NAV_Q, RETRIEVER.retrieve(NAV_Q), client=client)
    assert not a.abstained and a.attempts == 2 and "higher" not in a.text
    assert "'higher'" in client.calls[1]["messages"][-1]["content"]


def test_ungrounded_direction_twice_abstains():
    bad = _reply("A different, often higher NAV may apply.")
    a = llm.generate_answer(NAV_Q, RETRIEVER.retrieve(NAV_Q), client=FakeClient([bad, bad]))
    assert a.abstained


def test_missing_key_raises_clear_error(monkeypatch):
    monkeypatch.setattr(llm, "_client", None)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(llm.MissingAPIKeyError):
        llm.generate_answer("What is exit load?", _hits())
