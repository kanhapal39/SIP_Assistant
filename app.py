"""Streamlit chat UI for SIP Assistant. Run with: streamlit run app.py"""

import html
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

# On Streamlit Community Cloud the key lives in the app's Secrets. Bridge it
# into the environment before llm.py reads it. Locally, .env is used instead.
if not os.environ.get("GROQ_API_KEY"):
    try:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

import guardrails  # noqa: E402
import llm  # noqa: E402
import pipeline  # noqa: E402
from retrieval import Retriever  # noqa: E402

DISCLAIMER = (
    "This assistant explains SIP mechanics and terminology. "
    "It does not give investment advice."
)
INTRO = "Plain-language help with SIP terms and common SIP mechanics, for first-time investors in India."

# Starter rows under the greeting (icon, question) — all verified to route to an answer.
STARTERS = [
    ("💡", "What is XIRR?"),
    ("⚠️", "Why did my SIP payment fail?"),
    ("🏷️", "What is exit load?"),
]

# Quick-action chips above the input. Each opens a tray of example questions,
# except "Why no advice?", which shows the guardrail's own refusal copy.
QUICK_ACTIONS = {
    "glossary": ("Glossary", "📖", [
        "What is XIRR?", "What is CAGR?", "What is an expense ratio?", "What is a step-up SIP?",
    ]),
    "mechanics": ("SIP mechanics", "⚙️", [
        "Why would my SIP payment fail?",
        "I cancelled my SIP but money still got deducted — why?",
        "How do I change my SIP amount or date?",
        "How does UPI AutoPay work for SIPs?",
    ]),
}
WHY_NO_ADVICE_Q = "Why can't you give investment advice?"

# Short card headlines for the non-answer states (labels only, no claims).
HEADLINES = {
    "refuse": "No investment advice",
    "personal_data": "Account data not available",
    "named_fund": "Fund details not available",
    "abstain": "Outside my scope",
    "error": "Something went wrong",
}

IST = ZoneInfo("Asia/Kolkata")
PRIMARY = "#0D7A5F"


def _svg(paths: str, stroke: str, size: int = 18) -> str:
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{stroke}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>')


LEAF = '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>'
SHIELD = '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
SHIELD_CHECK = SHIELD + '<path d="m9 12 2 2 4-4"/>'
USER = '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/>'
HAND = '<path d="M18 11V6a2 2 0 0 0-4 0v5"/><path d="M14 10V4a2 2 0 0 0-4 0v6"/><path d="M10 10.5V6a2 2 0 0 0-4 0v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/>'
ALERT = '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>'
CAL = '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>'
DOC = '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>'
THUMB_UP = '<path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/>'
THUMB_DOWN = '<path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/>'
COPY = '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>'
BULB = '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6M10 22h4"/>'

SEND_ICON = (
    "data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
    "stroke='white' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E"
    "%3Cpath d='M12 19V5'/%3E%3Cpath d='m5 12 7-7 7 7'/%3E%3C/svg%3E"
)
CHAT_ICON = (
    "data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
    "stroke='%2364748B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E"
    "%3Cpath d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'/%3E"
    "%3Cpath d='M8 9h8M8 13h5'/%3E%3C/svg%3E"
)

# Design tokens from the "Calm Wealth Assistant" DESIGN.md; layout from the Stitch screens.
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
:root {{
  --primary: {PRIMARY}; --primary-hover: #0A604B; --primary-soft: #E6F4F0; --mint: #98F4D3;
  --canvas: #F4F9F6; --surface: #FFFFFF; --tint: #F2F3FF; --line: #E6EFEA; --chip-line: #D1E3DA;
  --input-line: #CBDCD3; --text: #0F172A; --text-2: #64748B;
  --info-bg: #EFF6FF; --info-line: #BFDBFE; --info-text: #1E40AF; --info-head: #1E3A8A;
  --warn-bg: #FEF3C7; --warn-line: #FDE68A; --warn-text: #92400E; --warn-head: #78350F;
  --shadow-1: 0 4px 20px -2px rgba(15,118,110,0.06);
  --shadow-2: 0 12px 32px -4px rgba(15,118,110,0.10);
}}
.stApp, .stApp *:not([data-testid="stIconMaterial"]) {{ font-family:'Plus Jakarta Sans', sans-serif; }}
.stApp {{ background:var(--canvas); color:var(--text); }}

/* Single-screen chat: no Streamlit toolbar, no sidebar, 480px column (DESIGN.md). */
header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"] {{ display:none !important; }}
.block-container, [data-testid="stBottomBlockContainer"] {{ max-width:512px; padding-left:1rem; padding-right:1rem; }}
.block-container {{ padding-top:0 !important; padding-bottom:1.5rem !important; }}

/* Header: primary band across the chat column, edge to edge, pinned to the top.
   Streamlit wraps layout containers in a same-height stLayoutWrapper, so pin and size that. */
[data-testid="stLayoutWrapper"]:has(> .st-key-hdr) {{ position:sticky; top:0; z-index:50; margin:0 -1rem !important;
  width:calc(100% + 2rem) !important; max-width:none !important; }}
.st-key-hdr {{ width:100% !important; }}
/* Streamlit gives markdown a negative bottom margin; undo it so the band fits its content. */
.st-key-hdr [data-testid="stMarkdown"], .st-key-hdr [data-testid="stMarkdownContainer"] {{ margin:0 !important; }}
.st-key-hdr {{ background:var(--primary); padding:14px 16px; gap:8px !important; flex-wrap:nowrap !important;
  align-items:center; box-shadow:var(--shadow-2); }}
.st-key-hdr > [data-testid="stElementContainer"] {{ width:auto !important; flex:0 0 auto; }}
.st-key-hdr > [data-testid="stElementContainer"]:first-child {{ flex:0 1 auto; min-width:0; }}
.st-key-hdr > [data-testid="stElementContainer"]:last-child {{ margin-left:auto; }}
.st-key-hdr .st-key-clear {{ align-self:flex-end; margin-bottom:1px; }}
.sa-hdr {{ display:flex; align-items:center; gap:12px; min-width:0; }}
.sa-hdr-av {{ position:relative; width:46px; height:46px; border-radius:50%; background:rgba(255,255,255,.18);
  display:flex; align-items:center; justify-content:center; flex:0 0 auto; }}
.sa-dot {{ display:inline-block; flex:0 0 auto; width:8px; height:8px; border-radius:50%; background:#4ADE80; }}
.sa-hdr-av .sa-dot {{ position:absolute; right:1px; bottom:2px; width:11px; height:11px; border:2px solid var(--primary); }}
.sa-title {{ color:#fff; font-size:20px; font-weight:700; line-height:26px; letter-spacing:-0.01em; display:flex; align-items:center; gap:8px; white-space:nowrap; }}
.sa-badge {{ font-size:11px; font-weight:600; letter-spacing:0.02em; background:rgba(255,255,255,.16); color:#C8F5E4;
  padding:2px 8px; border-radius:6px; }}
.sa-status {{ font-size:13px; font-weight:500; line-height:17px; color:#BFF3E0; display:flex; align-items:center; gap:6px; margin-top:2px; }}
.sa-hdr-icons {{ display:flex; gap:8px; }}
.sa-hdr-icons span {{ width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; }}
.sa-hdr-icons .shield {{ background:rgba(255,255,255,.16); }}
.sa-hdr-icons .profile {{ background:#0A4A3A; }}
.st-key-clear button {{ width:24px; height:24px; min-height:0; padding:0; border-radius:50%;
  background:rgba(255,255,255,.18); border:none; color:#fff; }}
.st-key-clear button:hover {{ background:rgba(255,255,255,.32); color:#fff; }}
.st-key-clear button p {{ display:none; }}
.st-key-clear [data-testid="stIconMaterial"] {{ font-size:16px; }}
@media (max-width: 440px) {{
  .sa-badge {{ display:none; }}
  .sa-hdr {{ gap:10px; }}
  .sa-hdr-av {{ width:40px; height:40px; }}
  .sa-hdr-icons {{ gap:6px; }}
  .sa-hdr-icons span {{ width:34px; height:34px; }}
  .sa-status {{ font-size:12px; line-height:15px; }}
}}

/* Date pill */
.sa-pill {{ display:flex; justify-content:center; margin:14px 0 6px; }}
.sa-pill span {{ display:inline-flex; align-items:center; gap:6px; background:#E2E7FF; color:#283044;
  font-size:12px; font-weight:600; letter-spacing:0.01em; padding:5px 14px; border-radius:9999px; }}

/* Messages */
.sa-row {{ display:flex; gap:10px; margin:12px 0 2px; align-items:flex-start; }}
.sa-row.user {{ justify-content:flex-end; }}
.sa-av {{ position:relative; flex:0 0 auto; width:34px; height:34px; border-radius:50%; background:var(--primary-soft);
  display:flex; align-items:center; justify-content:center; }}
.sa-av.refuse {{ background:#7C3A0A; }} .sa-av.abstain {{ background:#DBE4FF; }} .sa-av.error {{ background:#FDECEC; }}
.sa-col {{ max-width:85%; display:flex; flex-direction:column; }}
.sa-row.user .sa-col {{ align-items:flex-end; }}
.sa-bubble {{ padding:13px 16px; font-size:15px; line-height:24px; color:var(--text); background:var(--surface);
  border:1px solid var(--line); border-radius:18px; border-top-left-radius:4px; box-shadow:var(--shadow-1); }}
.sa-bubble.user {{ background:var(--mint); border-color:#7CD8B8; border-radius:18px; border-bottom-right-radius:4px; box-shadow:none; }}
.sa-meta {{ font-size:11px; font-weight:600; letter-spacing:0.04em; color:var(--text-2); margin:4px 4px 0; }}
.sa-card-foot {{ display:flex; justify-content:flex-end; margin-top:8px; font-size:11px; font-weight:600;
  letter-spacing:0.04em; color:var(--text-2); }}
.sa-source {{ display:flex; align-items:center; gap:6px; margin:8px 0 0 4px; font-size:12px; font-weight:500; color:var(--text-2); }}
.sa-actions {{ display:flex; gap:8px; margin:8px 0 0 2px; }}
.sa-actions span {{ display:inline-flex; align-items:center; gap:6px; padding:5px 12px; border-radius:9999px;
  background:var(--surface); border:1px solid var(--line); font-size:12px; font-weight:500; color:#3E4944; }}

/* Greeting card */
.sa-greet {{ background:var(--tint); border:1px solid #E2E7FF; border-radius:20px; border-top-left-radius:4px; padding:20px; }}
.sa-greet h3 {{ font-size:24px; font-weight:700; line-height:32px; letter-spacing:-0.015em; margin:0 0 10px; padding:0; color:var(--text); }}
.sa-greet p {{ font-size:16px; line-height:26px; color:#3E4944; margin:0 0 16px; }}
.sa-inner {{ background:var(--surface); border-radius:16px; padding:14px 16px; box-shadow:var(--shadow-1); }}
.sa-inner b {{ display:block; color:var(--primary); font-size:15px; font-weight:700; margin-bottom:4px; }}
.sa-inner span {{ font-size:14px; line-height:22px; color:#283044; }}
.sa-greet-foot {{ display:flex; justify-content:space-between; align-items:center; margin-top:14px; font-size:13px; font-weight:600; }}
.sa-greet-foot .ready {{ color:var(--primary); display:flex; align-items:center; gap:6px; }}
.sa-greet-foot .ready .sa-dot {{ background:var(--primary); }}
.sa-greet-foot .time {{ color:var(--text-2); }}

/* Refusal / abstention cards */
.sa-bubble.refuse {{ background:var(--warn-bg); border-color:var(--warn-line); color:var(--warn-text); padding:12px; }}
.sa-bubble.abstain {{ background:var(--info-bg); border-color:var(--info-line); color:var(--info-text); padding:12px; }}
.sa-bubble.error {{ background:#FDECEC; border-color:#F5C2C2; color:#93000A; padding:12px; }}
.sa-head {{ display:flex; align-items:center; gap:10px; font-size:18px; font-weight:700; line-height:24px; border-radius:12px;
  padding:10px 12px; margin-bottom:10px; }}
.refuse .sa-head {{ background:#FDE2B3; color:var(--warn-head); }}
.abstain .sa-head {{ color:var(--info-head); padding:4px 4px 0; }}
.error .sa-head {{ color:#93000A; padding:4px 4px 0; }}
.sa-body {{ padding:0 4px; }}
.refuse .sa-card-foot, .abstain .sa-card-foot {{ padding:0 4px; }}
.sa-typing {{ color:var(--text-2); font-style:italic; }}

/* Suggested questions */
.sa-sugg {{ display:flex; justify-content:space-between; align-items:center; margin:22px 2px 8px; font-size:15px; color:#283044; }}
.sa-sugg span {{ display:flex; align-items:center; gap:8px; }}
.sa-sugg em {{ font-style:normal; font-size:13px; color:var(--text-2); }}
.st-key-starters {{ gap:10px !important; }}
.st-key-starters button {{ justify-content:flex-start; border-radius:9999px; background:var(--surface); border:1px solid var(--line);
  padding:14px 20px; min-height:0; box-shadow:var(--shadow-1); color:var(--text); }}
.st-key-starters button p {{ font-size:15px; font-weight:500; text-align:left; }}
.st-key-starters button::after {{ content:"→"; margin-left:auto; font-size:18px; color:var(--text-2); }}
.st-key-starters button:hover {{ border-color:var(--primary); color:var(--primary); box-shadow:var(--shadow-2); }}

/* Quick-action chips and their tray: one row, scrolls sideways on narrow screens */
.st-key-quick, .st-key-tray {{ gap:8px !important; flex-wrap:nowrap !important; overflow-x:auto; padding-bottom:2px; scrollbar-width:none; }}
.st-key-quick [data-testid="stElementContainer"], .st-key-tray [data-testid="stElementContainer"] {{ flex:0 0 auto; width:auto !important; }}
.st-key-quick button, .st-key-tray button {{ border-radius:9999px; background:var(--surface); border:1px solid var(--line);
  padding:7px 14px; min-height:0; box-shadow:var(--shadow-1); color:var(--text); white-space:nowrap; }}
.st-key-quick button p, .st-key-tray button p {{ font-size:13px; font-weight:600; white-space:nowrap; }}
.st-key-tray button {{ background:var(--primary-soft); border-color:var(--chip-line); color:var(--primary); }}
.st-key-quick button:hover, .st-key-tray button:hover {{ border-color:var(--primary); color:var(--primary); }}

/* Bottom bar: frosted canvas, pill input with chat icon, round primary send */
[data-testid="stBottom"] > div {{ background:rgba(244,249,246,0.9); backdrop-filter:blur(12px); }}
[data-testid="stChatInput"] {{ border-radius:9999px !important; border:1px solid var(--input-line) !important;
  background:var(--surface) url("{CHAT_ICON}") 16px center/22px no-repeat !important; box-shadow:var(--shadow-2); padding-left:44px; }}
[data-testid="stChatInput"]:focus-within {{ border:2px solid var(--primary) !important; box-shadow:0 0 0 4px rgba(13,122,95,0.12), var(--shadow-2); }}
[data-testid="stChatInput"] textarea {{ font-size:15px; color:var(--text); }}
[data-testid="stChatInputSubmitButton"] {{ border-radius:50% !important; width:44px !important; height:44px !important;
  background:var(--primary) url("{SEND_ICON}") center/22px no-repeat !important; opacity:1; }}
[data-testid="stChatInputSubmitButton"]:hover {{ background-color:var(--primary-hover) !important; }}
[data-testid="stChatInputSubmitButton"]:disabled {{ background-color:#0A4A3A !important; }}
[data-testid="stChatInputSubmitButton"] svg {{ display:none; }}
[data-testid="stBottomBlockContainer"]::after {{ content:"ⓘ  {DISCLAIMER}"; display:block; text-align:center;
  font-size:11px; font-weight:500; letter-spacing:0.01em; color:var(--text-2); margin-top:8px; }}
</style>
"""


@st.cache_resource
def get_retriever() -> Retriever:
    return Retriever()


def _now() -> str:
    return datetime.now(IST).strftime("%-I:%M %p")


def _esc(text: str) -> str:
    # Escape for HTML, keep line breaks, and stop Streamlit reading $…$ as LaTeX.
    return html.escape(text).replace("\n", "<br>").replace("$", "&#36;")


def _html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def _headline(msg: dict) -> str:
    rule = msg.get("rule") or ""
    if msg["kind"] == pipeline.ABSTAIN:
        for key in ("personal_data", "named_fund"):
            if rule.startswith(key):
                return HEADLINES[key]
    return HEADLINES.get(msg["kind"], "")


def render(msg: dict) -> None:
    time = msg.get("time", "")
    if msg["role"] == "user":
        _html(f'<div class="sa-row user"><div class="sa-col"><div class="sa-bubble user">{_esc(msg["text"])}</div>'
              f'<div class="sa-meta">{time} · Delivered ✓✓</div></div></div>')
        return

    kind = msg.get("kind")
    if kind == pipeline.ANSWER:
        avatar = f'<div class="sa-av">{_svg(LEAF, PRIMARY)}</div>'
        card = (f'<div class="sa-bubble">{_esc(msg["text"])}'
                f'<div class="sa-card-foot">{time}</div></div>')
        if msg.get("source_title"):
            card += f'<div class="sa-source">{_svg(DOC, "#64748B", 14)}Source: {_esc(msg["source_title"])}</div>'
        # Decorative feedback row, as in the mockup — not wired to anything.
        card += (f'<div class="sa-actions"><span>{_svg(THUMB_UP, "#3E4944", 14)}Helpful</span>'
                 f'<span>{_svg(THUMB_DOWN, "#3E4944", 14)}</span><span>{_svg(COPY, "#3E4944", 14)}Copy</span></div>')
    else:
        icon, av_icon = {
            pipeline.REFUSE: (_svg(HAND, "#B45309", 22), _svg(SHIELD, "#FDE68A")),
            pipeline.ABSTAIN: (_svg(SHIELD, "#2563EB", 22), _svg(SHIELD, "#2563EB")),
        }.get(kind, (_svg(ALERT, "#BA1A1A", 22), _svg(ALERT, "#BA1A1A")))
        avatar = f'<div class="sa-av {kind}">{av_icon}</div>'
        card = (f'<div class="sa-bubble {kind}"><div class="sa-head">{icon}{_esc(_headline(msg))}</div>'
                f'<div class="sa-body">{_esc(msg["text"])}</div><div class="sa-card-foot">{time}</div></div>')
    _html(f'<div class="sa-row">{avatar}<div class="sa-col">{card}</div></div>')


def respond(question: str) -> dict:
    try:
        r = pipeline.run(question, get_retriever())
    except llm.MissingAPIKeyError:
        return {"kind": "error", "text": "The assistant isn't configured yet (missing GROQ_API_KEY)."}
    except Exception:
        return {"kind": "error", "text": "Something went wrong reaching the language model. Please try again in a moment."}
    return {"kind": r.kind, "text": r.text, "source_title": r.source_title, "rule": r.rule}


def ask(q: str) -> None:
    st.session_state.pending = q
    st.session_state.tray = None


def toggle_tray(name: str) -> None:
    st.session_state.tray = None if st.session_state.get("tray") == name else name


def why_no_advice() -> None:
    st.session_state.tray = None
    t = _now()
    st.session_state.messages += [
        {"role": "user", "text": WHY_NO_ADVICE_Q, "time": t},
        {"role": "assistant", "kind": pipeline.REFUSE, "text": guardrails.REFUSAL_MESSAGE,
         "source_title": None, "rule": "guardrails", "time": t},
    ]


def clear_chat() -> None:
    st.session_state.messages = []
    st.session_state.tray = None


st.set_page_config(page_title="SIP Assistant", page_icon="📘", layout="centered", initial_sidebar_state="collapsed")
_html(CSS)

st.session_state.setdefault("messages", [])
st.session_state.setdefault("tray", None)
st.session_state.setdefault("started", _now())

# Bottom area (pinned above the input): optional tray, quick-action chips, input.
bottom = st._bottom if hasattr(st, "_bottom") else st.container()
with bottom:
    tray = st.session_state.tray
    if tray in QUICK_ACTIONS:
        with st.container(key="tray", horizontal=True):
            for i, q in enumerate(QUICK_ACTIONS[tray][2]):
                st.button(q, key=f"tray_{tray}_{i}", on_click=ask, args=(q,))
    with st.container(key="quick", horizontal=True):
        for name, (label, icon, _) in QUICK_ACTIONS.items():
            st.button(label, key=f"qa_{name}", icon=icon, on_click=toggle_tray, args=(name,))
        st.button("Why no advice?", key="qa_advice", icon="⚖️", on_click=why_no_advice)
    typed = st.chat_input("Ask about SIPs, NAV, XIRR…")

question = typed or st.session_state.pop("pending", None)
if question:
    st.session_state.messages.append({"role": "user", "text": question, "time": _now()})

# Header band: avatar | title + status with clear-chat icon | decorative shield/profile icons.
with st.container(key="hdr", horizontal=True):
    _html(f'<div class="sa-hdr"><div class="sa-hdr-av">{_svg(LEAF, "#fff", 22)}<span class="sa-dot"></span></div><div>'
          f'<div class="sa-title">SIP Assistant <span class="sa-badge">Assistant Chat</span></div>'
          f'<div class="sa-status"><span class="sa-dot"></span>Online · SIP terms &amp; mechanics only</div></div></div>')
    st.button("Clear chat", key="clear", icon=":material/delete_sweep:", help="Clear chat", on_click=clear_chat)
    _html(f'<div class="sa-hdr-icons"><span class="shield">{_svg(SHIELD_CHECK, "#BFF3E0")}</span>'
          f'<span class="profile">{_svg(USER, "#fff")}</span></div>')

_html(f'<div class="sa-pill"><span>{_svg(CAL, "#283044", 14)}Today · {st.session_state.started}</span></div>')

# Greeting: existing intro + disclaimer copy, always first in the conversation.
_html(f'<div class="sa-row"><div class="sa-av">{_svg(LEAF, PRIMARY)}<span class="sa-dot" '
      f'style="position:absolute;right:-1px;bottom:-1px;width:10px;height:10px;background:{PRIMARY};border:2px solid #F4F9F6"></span></div>'
      f'<div class="sa-col" style="max-width:100%"><div class="sa-greet"><h3>Welcome to SIP Assistant 👋</h3>'
      f'<p>{_esc(INTRO)}</p><div class="sa-inner"><b>Educational only</b><span>{_esc(DISCLAIMER)}</span></div>'
      f'<div class="sa-greet-foot"><span class="ready"><span class="sa-dot"></span>Ready to help</span>'
      f'<span class="time">{st.session_state.started}</span></div></div></div></div>')

if not st.session_state.messages:
    _html(f'<div class="sa-sugg"><span>{_svg(BULB, PRIMARY)}Suggested questions to start</span><em>Tap to ask</em></div>')
    with st.container(key="starters"):
        for i, (icon, q) in enumerate(STARTERS):
            st.button(q, key=f"starter_{i}", icon=icon, use_container_width=True, on_click=ask, args=(q,))

for m in st.session_state.messages:
    render(m)

if question:
    slot = st.empty()
    slot.markdown(f'<div class="sa-row"><div class="sa-av">{_svg(LEAF, PRIMARY)}</div>'
                  f'<div class="sa-bubble"><span class="sa-typing">Looking that up…</span></div></div>',
                  unsafe_allow_html=True)
    reply = {"role": "assistant", "time": _now(), **respond(question)}
    slot.empty()
    render(reply)
    st.session_state.messages.append(reply)
