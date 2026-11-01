import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import boundaries  # noqa: E402
import guardrails  # noqa: E402
import retrieval  # noqa: E402

GOLDEN = os.path.join(os.path.dirname(__file__), "..", "eval", "golden_set.yaml")
ITEMS = yaml.safe_load(open(GOLDEN, encoding="utf-8"))["items"]
RETRIEVER = retrieval.Retriever()


def test_corpus_loads_all_docs():
    ids = {d.doc_id for d in RETRIEVER.docs}
    assert len(ids) == 13
    assert "faq/nav_allocation_timing.md" in ids
    assert all(d.title and d.body for d in RETRIEVER.docs)


@pytest.mark.parametrize("item", [i for i in ITEMS if i["category"] == "answerable"], ids=lambda i: i["id"])
def test_answerable_retrieves_expected_doc(item):
    assert not boundaries.check(item["question"]).blocked
    hits = RETRIEVER.retrieve(item["question"])
    assert hits, f"below threshold: {RETRIEVER.search(item['question'])[0].score:.3f}"
    assert hits[0].doc.doc_id == item["expected_source"]


@pytest.mark.parametrize("item", [i for i in ITEMS if i["category"] == "should_abstain"], ids=lambda i: i["id"])
def test_should_abstain_is_stopped(item):
    q = item["question"]
    assert not guardrails.check(q).blocked
    assert boundaries.check(q).blocked or not RETRIEVER.retrieve(q)


@pytest.mark.parametrize("q,kind", [
    ("What's my current XIRR?", "personal_data"),
    ("Why was my specific SIP payment on 15th May not deducted?", "personal_data"),
    ("My SIP didn't go through on March 3rd", "personal_data"),
    ("Was the debit on 05/06/2026 processed?", "personal_data"),
    ("Can you check my account?", "personal_data"),
    ("Why did this transaction fail?", "personal_data"),
    ("The app crashed when I opened my portfolio", "personal_data"),
    ("What's the expense ratio of Parag Parikh Flexi Cap Fund?", "named_fund"),
    ("exit load for parag parikh flexi cap?", "named_fund"),
    ("What is the NAV of HDFC Flexi Cap?", "named_fund"),
    ("What's the XIRR of Zephyr Growth Fund?", "named_fund"),
])
def test_boundary_catches(q, kind):
    r = boundaries.check(q)
    assert r.blocked and r.kind == kind


@pytest.mark.parametrize("q", [
    "Why would my SIP payment fail even though I have enough balance in my account?",
    "I bought at one NAV but got a different, higher NAV value — why?",
    "What is a mutual fund?",
    "What is an Index Fund?",
    "My SBI mandate failed, why?",
    "How does UPI AutoPay work with my HDFC bank account?",
    "What is XIRR?",
    "May I know what a step-up SIP is?",
])
def test_boundary_allows(q):
    r = boundaries.check(q)
    assert not r.blocked, f"{r.kind}/{r.rule}"
