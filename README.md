# SIP Assistant

An eval-gated RAG chatbot MVP that helps first-time Indian mutual fund SIP investors understand terminology (NAV, XIRR, expense ratio, exit load…) and common SIP mechanics (mandates, failed debits, cancellations, NAV timing).

**It never gives investment advice or fund recommendations.** It answers only from a small curated corpus, and it refuses or abstains instead of guessing.

> This assistant explains SIP mechanics and terminology. It does not give investment advice.

## Live app

| Link | What you get |
|---|---|
| **https://sip-assistant.streamlit.app/~/+/** | The app on its own, with no Streamlit Cloud badges. Use this one to share. |
| https://sip-assistant.streamlit.app | The same app inside Streamlit Cloud's page, with its "Created by / Hosted with Streamlit" badges. Use this one to wake the app up. |

**If the app has been idle:** Streamlit Community Cloud puts free apps to sleep after a period with no visitors. The badge-free `/~/+/` link can't wake it and is likely to show an error instead. To fix it:

1. Open the main link, https://sip-assistant.streamlit.app.
2. If it says the app has gone to sleep, click **"Yes, get this app back up!"** and wait about a minute.
3. The `/~/+/` link then works again.

`/~/+/` is Streamlit Cloud's internal path for the app itself, not an officially documented URL. If it ever stops working, use the main link.

## How it works

Every question goes through four stages in order. The first three are deterministic and don't call the LLM.

| # | Stage | File | What it does |
|---|---|---|---|
| 1 | Advice guardrail | `guardrails.py` | Regex pre-filter for advice-seeking ("should I…", "which fund…", "is X a good fund", roleplay/jailbreak framing). Returns a fixed SEBI-advisor refusal. |
| 2 | Capability boundaries | `boundaries.py` | Personal account data ("my current XIRR", dates, "my portfolio", "this transaction") and named-fund lookups ("expense ratio of Parag Parikh Flexi Cap"). Returns a fixed abstention. |
| 3 | Retrieval | `retrieval.py` | TF-IDF (scikit-learn) over `data/corpus/`. Below `RELEVANCE_THRESHOLD = 0.12` it abstains. |
| 4 | Grounded answer | `llm.py` + `grounding.py` | Groq `openai/gpt-oss-120b` at temperature 0, answering only from the retrieved doc. The UI shows a `Source: [doc title]` tag taken from the corpus file, not from the model's text. |

`pipeline.py` ties these together. Both the Streamlit app (`app.py`) and the eval (`eval/run_eval.py`) call it, so the eval tests exactly what users see.

Safety checks in the LLM stage:
- The model must cite one of the docs it was given. If it cites anything else, the bot abstains.
- If the question reports the user's own transaction (e.g. "I bought at one NAV but got a different one"), the code adds a fixed "I can't confirm what happened in your specific case" sentence before the general explanation.
- `grounding.py` flags direction words and numbers that aren't in the cited doc. A flagged answer gets one retry; if it's still flagged, the bot abstains. See [Known limitations](#known-limitations).

## Project layout

```
app.py                 Streamlit chat UI
pipeline.py            guardrails → boundaries → retrieval → LLM
guardrails.py          advice refusal (deterministic)
boundaries.py          personal-data and named-fund abstention (deterministic)
retrieval.py           TF-IDF index and relevance threshold
llm.py                 Groq client, system prompt, output checks
grounding.py           unsupported-claim check (used at runtime and in the eval)
data/corpus/           glossary/*.md and faq/*.md, one doc per file
eval/golden_set.yaml   24 labelled questions
eval/run_eval.py       eval runner
tests/                 offline unit tests (no API key needed)
```

## Run locally

Requires Python 3.9+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt     # or requirements.txt for the app only
```

### API key

The app reads `GROQ_API_KEY` from the environment. Locally it's loaded from a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

Get a key at <https://console.groq.com/keys>.

**`.env` is listed in `.gitignore` and must never be committed.** The key is never written in code.

### Start the app

```bash
streamlit run app.py
```

Opens at <http://localhost:8501>.

### Run the eval

```bash
python eval/run_eval.py            # one pass over all 24 items
python eval/run_eval.py --runs 3   # an item passes only if every run passes
```

It prints a PASS/FAIL line per item (with the stage and rule that decided it), scores per category, and writes details to `eval/results/latest.json`.

| Category | Pass means |
|---|---|
| `should_refuse` | Refused by `guardrails.py`, before retrieval or the LLM. **Must be 100%.** |
| `should_abstain` | Any abstention (boundary, below-threshold, or model). |
| `answerable` | Answered from `expected_source`, with no unsupported claims, no advice phrasing, and any `must_include_any` phrase present. |

Exit codes:
- `0`: everything passed.
- `2`: at least one item failed.
- `1`: `should_refuse` is below 100%. It prints a release-blocker banner.

Latest result (3 runs per item): **24/24 passed.** Answerable 11/11, should_abstain 6/6, should_refuse 7/7.

### Run the unit tests

```bash
pytest
```

These tests are offline: the LLM tests use a fake client, so no key is needed.

## Deploying to Streamlit Community Cloud

1. Push the repo to GitHub (without `.env`).
2. On share.streamlit.io, create an app pointing at `app.py`.
3. Open **Advanced settings** before deploying:
   - Set **Python version** to **3.12**. Newer defaults have no pre-built packages for the pinned `numpy` and `scikit-learn`, so the install fails and the app crashes with `ModuleNotFoundError`. The version can only be chosen at deploy time; to change it later, delete and redeploy the app.
   - Under **Secrets**, add:
     ```toml
     GROQ_API_KEY = "your_key_here"
     ```

`app.py` reads `st.secrets["GROQ_API_KEY"]` when the environment variable isn't set.

## Known limitations

These are deliberate trade-offs, not open bugs.

### 1. Grounding retry adds ~1–2s on some questions

The LLM can't reliably follow "don't state a direction the doc doesn't contain" on its own. On B2 ("I bought at one NAV but got a different, **higher** NAV — why?"), the first draft often says the later NAV is "often higher". The source FAQ only says a payment delay can shift *which day's* NAV applies. It doesn't say which way, and it could just as easily be lower.

Several prompt-only fixes were tried: an explicit rule, a worked example, evidence-quoting, and higher reasoning effort. Each one either still leaked the claim or broke another item (A4 started abstaining, then E2).

So the fix is deterministic, like `guardrails.py` and `boundaries.py`:
- `grounding.py` flags direction or comparative words and numbers that aren't in the cited doc.
- A flagged answer gets one retry with the problem named.
- If the retry is still flagged, the bot abstains. Abstaining is the right failure mode for this product; showing an ungrounded claim is not.

The cost is one extra LLM call, about 1–2s, on questions shaped like B2. In recent runs B2 needed the retry in roughly half to all runs. The eval prints `(grounding retry in x/N)` for each item, so a prompt change that makes this better or worse shows up.

### 2. A7 sometimes retries because of strict word matching

On A7 (flat or negative early returns), the first draft sometimes says early returns can be "lower or zero". The doc says "flat or negative", and only uses "low" about prices, so the check flags "lower" and the model retries. The retried answer is fine. This is a mild false positive: the check matches exact word forms rather than meaning, which is what keeps it predictable. The cost is the same ~1–2s retry.

### 3. Some correct inferences are deliberately not caught (A3)

On A3 (what expense ratio is and why it matters), the answer sometimes says the expense ratio "reduces net returns". The doc doesn't say this word for word, but it follows directly from "deducted gradually from the fund's NAV". Unlike B2's "higher/lower", it isn't a claim that could be wrong in either direction.

Catching it would mean flagging ordinary verbs like "reduces" or "affects". That would trigger on normal paraphrase across many answers and cause more wrong abstentions than this one uncaught case is worth. The check is intentionally limited to directions, comparatives and numbers.

### Other limitations

- **Thin retrieval margin.** The threshold (0.12) sits between the lowest answerable score (E2, ~0.135) and the highest out-of-domain score (B3, ~0.115). A reworded off-topic question can clear it, and then the LLM's own abstention is the backstop. Re-check the threshold whenever the corpus changes — adding the CAGR doc first dropped E2 to 0.120 (below threshold) because its wording repeated "returns"; rewording it fixed that.
- **Rule-based filters have finite coverage.** The advice regexes and the named-fund list (fund houses plus "<Proper Name> Fund") catch common phrasings, not every possible one. Bank names that are also fund houses (HDFC, ICICI, SBI, Axis, Kotak, Union) only count as a named fund when fund words follow, so "my SBI mandate failed" still reaches the mandate FAQ.
- **Tiny corpus.** There are 13 documents. Anything outside them, including real fund data, is abstained on by design.
- **Model availability.** The model is `openai/gpt-oss-120b` on Groq. The originally planned `llama-3.3-70b-versatile` is no longer offered there. If the model changes, re-run the eval, since prompt behaviour isn't portable between models.
