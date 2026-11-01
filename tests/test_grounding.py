import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import grounding  # noqa: E402

NAV_DOC = ("The NAV applied to a mutual fund purchase depends on when the payment amount is actually "
           "realised in the scheme's account relative to that scheme's daily cut-off time (commonly 3 PM "
           "for equity funds). A delay in payment clearing can shift which day's NAV applies.")
NAV_Q = "I bought at one NAV but got a different, higher NAV value — why?"
RCA_DOC = "It naturally buys more units when prices are low and fewer when prices are high."


@pytest.mark.parametrize("answer,expected", [
    ("A later day's NAV may apply, which could be higher.", ["higher"]),
    ("A different, often higher NAV may be used.", ["higher"]),
    ("It may lead to a lower NAV.", ["lower"]),
    ("The cut-off is often 4 PM.", ["4"]),
    ("Returns of 12% are typical.", ["12%"]),
])
def test_flags_unsupported(answer, expected):
    assert grounding.unsupported_claims(answer, NAV_DOC, NAV_Q) == expected


@pytest.mark.parametrize("answer,doc,q", [
    ("A delay can shift which day's NAV applies, so it may differ.", NAV_DOC, NAV_Q),
    ("The cut-off is commonly 3 PM for equity funds.", NAV_DOC, NAV_Q),
    ("A SIP buys more units when prices are low and fewer when high.", RCA_DOC, ""),
    ("No — SIPs don't guarantee 15% returns.", RCA_DOC, "I heard SIPs guarantee 15% returns — is that true?"),
])
def test_allows_supported(answer, doc, q):
    assert grounding.unsupported_claims(answer, doc, q) == []
