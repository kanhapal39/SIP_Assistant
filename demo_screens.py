"""Demo investment-app screens: Explore, Dashboard, Profile, SIP sheet, exit survey.

Everything here is invented sample data and does not touch the answer pipeline.
The only hand-off is "Start a SIP" / "Start SIP", which opens the chat via a callback.

Navigation state lives in st.session_state:
  view   — "explore" | "dashboard" | "profile" (app.py owns "chat")
  sheet  — None | "fund" | "exit"   (bottom sheet over the Dashboard)
"""

from typing import Callable

import streamlit as st

VIEWS = ("explore", "dashboard", "profile")
START_SIP_QUESTION = "What is a systematic investment plan?"
DEMO_NOTE = "Demo data for illustration"

# ---- Invented sample data -------------------------------------------------
USER_NAME = "Demo Investor"
USER_INITIALS = "DI"
FUND_NAME = "Sample Flexi Cap Fund Direct Plan Growth"
# Internally consistent: 54,316 − 48,000 = 6,316 = 13.16% of invested.
HOLDINGS = {
    "count": 1, "value": "₹54,316", "day": "+₹312.40 (0.58%)", "total": "+₹6,316 (13.16%)",
    "invested": "₹48,000", "xirr": "11.42%", "fund_day": "+₹312.40", "fund_day_pct": "(+0.58%)",
}
BALANCES = [
    ("Stocks, F&amp;O balance", "₹2,450.00", "Add money"),
    ("Instant trade balance", "₹0.00", "Pledge"),
    ("US Stocks balance", "$0.00", "Activate"),
]

# ---- Icons (24px stroke paths) --------------------------------------------
SEARCH = '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.35-4.35"/>'
LOADER = ('<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4'
          'M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>')
USER = '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/>'
EYE = '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>'
BARS = '<path d="M8 20v-6M12 20V8M16 20v-9"/>'
CHEV_DOWN = '<path d="m6 9 6 6 6-6"/>'
CHEV_RIGHT = '<path d="m9 18 6-6-6-6"/>'
FILTER = '<path d="M4 6h16M7 12h10M10 18h4"/>'
SORT = '<path d="m8 7-5 5 5 5M16 7l5 5-5 5"/>'
DOWNLOAD = '<path d="M12 4v11M7 10l5 5 5-5"/><path d="M4 17v2a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-2"/>'
STOCKS = '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="m7 14 3-4 3 3 4-4"/>'
FNO = '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="m7 15 5-6 5 6"/>'
PIE = '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>'
LOANS = '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/>'
SPARKLE = '<path d="M12 2v20M2 12h20"/>'
BACK = '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>'
USER_PLUS = '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M19 8v6M22 11h-6"/>'
BELL = '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>'
GEAR = ('<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73'
        'l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38'
        'a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18'
        'a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08'
        'a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08'
        'a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>')
ORDERS = ('<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6'
          'a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M9 12h6M9 16h4"/>')
REPORTS = '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 18v-2M12 18v-4M16 18v-6"/>'
UPI = ('<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>'
       '<rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3M21 14v7h-7"/>')
BANK = '<path d="M3 22h18M6 18v-7M10 18v-7M14 18v-7M18 18v-7M12 2l9 5H3z"/>'
GIFT = ('<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M12 8v13M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/>'
        '<path d="M7.5 8a2.5 2.5 0 0 1 0-5C10 3 12 8 12 8s2-5 4.5-5a2.5 2.5 0 0 1 0 5"/>')
TREND = '<path d="m22 7-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/>'
CAL_CHECK = '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/><path d="m9 16 2 2 4-4"/>'
COINS = '<circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1 1 10.34 18"/><path d="M7 6h1v4"/>'
STAR = '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z"/>'
MIDCAP = '<path d="M3 3v18h18"/><path d="M8 17v-4M13 17V9M18 17v-6"/>'
SPROUT = ('<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/>'
          '<path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/>'
          '<path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>')
REDEEM = '<path d="M7 17 17 7M8 7h9v9"/>'
LIST = '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>'

# (name, 3Y return, icon, ink, tint)
POPULAR = [
    ("Sample Flexi Cap Fund", "18.62%", PIE, "#0D7A5F", "#E6F4F0"),
    ("Demo Mid Cap Fund", "24.31%", MIDCAP, "#3B4CCA", "#E2E7FF"),
    ("Sample Small Cap Fund", "27.94%", SPROUT, "#B45309", "#FEF3C7"),
    ("Demo Gold ETF", "16.20%", COINS, "#8A6D00", "#FFF4CC"),
]
COLLECTIONS = [
    ("High return", TREND), ("Best SIP funds", CAL_CHECK), ("Gold &amp; Silver Funds", COINS),
    ("5 Star Funds", STAR), ("Mid Cap", MIDCAP), ("Small Cap", SPROUT),
]
PROFILE_LINKS = [
    ("Orders", ORDERS), ("Reports", REPORTS), ("UPI", UPI), ("Account details", USER),
    ("Banks &amp; AutoPay", BANK), ("Refer &amp; Invite", GIFT),
]
EXIT_REASONS = [
    "Found a better option", "Need the money now", "Not seeing the returns I expected",
    "Something about this SIP is confusing me", "Other",
]
# Reasons that open the chat instead of closing: reason index → (opening line, tap-to-ask follow-ups).
# The follow-ups go through the normal pipeline; each was checked to retrieve a matching corpus doc.
CHAT_BRIDGES = {
    2: ("Before you go — let's see if I can help. Your SIP's return can look unusual in the short term "
        "for a few reasons — want me to walk through what's happening?",
        ["Is it normal for SIP returns to be low early on?", "What is XIRR?", "What is an expense ratio?"]),
    3: ("Before you go — let's see if I can help. What's confusing you about this SIP?",
        ["What is NAV?", "What is exit load?", "How do I change my SIP amount or date?"]),
}
CHECK = '<circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/>'

CALENDAR = (
    '<svg viewBox="0 0 120 120" width="104" height="104" fill="none" style="transform:rotate(-2deg)">'
    '<polygon fill="#E6EFEA" points="25,45 85,25 105,75 45,95"/>'
    '<polygon fill="#FFFFFF" stroke="#0A604B" stroke-width="2" points="20,40 80,20 100,70 40,90"/>'
    '<polygon fill="#2BB58E" stroke="#0A604B" stroke-width="1.5" points="20,40 80,20 86,35 26,55"/>'
    + "".join(f'<line stroke="#0A4A3A" stroke-linecap="round" stroke-width="2" x1="{x}" x2="{x - 2}" y1="{y}" y2="{y + 12}"/>'
              for x, y in ((33, 28), (48, 23), (63, 18), (77, 13)))
    + "".join(f'<rect fill="{c}" width="8" height="8" rx="1.5" x="{x}" y="{y}"/>'
              for x, y, c in ((36, 58, "#E6F4F0"), (50, 53, "#E6F4F0"), (64, 48, "#E6F4F0"), (78, 43, "#2BB58E"),
                              (42, 70, "#E6F4F0"), (56, 65, "#0D7A5F"), (70, 60, "#E6F4F0"), (84, 55, "#E6F4F0")))
    + '<polygon fill="#0A4A3A" points="18,44 40,94 40,97 16,46"/></svg>'
)
SPARKLINE = (
    '<svg viewBox="0 0 120 44" width="120" height="44" fill="none">'
    '<defs><linearGradient id="spk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0D7A5F" stop-opacity=".22"/>'
    '<stop offset="1" stop-color="#0D7A5F" stop-opacity="0"/></linearGradient></defs>'
    '<path d="M2 38 L18 33 L32 35 L48 26 L62 28 L78 18 L92 20 L106 9 L118 5 L118 44 L2 44 Z" fill="url(#spk)"/>'
    '<polyline points="2,38 18,33 32,35 48,26 62,28 78,18 92,20 106,9 118,5" stroke="#0D7A5F" stroke-width="2.2" '
    'stroke-linecap="round" stroke-linejoin="round"/><circle cx="118" cy="5" r="3" fill="#0D7A5F"/></svg>'
)

CSS = """
<style>
.stApp { background:var(--canvas); }
.block-container { padding-bottom:104px !important; }
.st-key-screen { gap:0 !important; }
.st-key-screen [data-testid="stMarkdown"], .st-key-screen [data-testid="stMarkdownContainer"],
.st-key-sheet [data-testid="stMarkdown"], .st-key-sheet [data-testid="stMarkdownContainer"] { margin:0 !important; }

/* Tap targets: visible HTML with an invisible full-size button laid over it. */
[class*="st-key-tap_"] { position:relative; gap:0 !important; border-radius:12px; }
[class*="st-key-tap_"]:has(button:focus-visible) { outline:2px solid var(--primary); outline-offset:2px; }
[class*="st-key-tb_"] { position:absolute !important; inset:0; z-index:5; margin:0 !important; width:100% !important; }
[class*="st-key-tb_"] div, [class*="st-key-tb_"] button { width:100% !important; height:100% !important; }
[class*="st-key-tb_"] button { opacity:0; min-height:0; padding:0; border:none; cursor:pointer; }

/* Header + tabs (Explore / Dashboard) */
.st-key-dhdr, .st-key-phdr, .st-key-dtabs { flex-wrap:nowrap !important; align-items:center; }
.st-key-dhdr > *, .st-key-phdr > *, .st-key-dtabs > * { width:auto !important; flex:0 0 auto; }
.st-key-dhdr { gap:18px !important; padding:16px 2px 6px; }
.st-key-dhdr > *:first-child { flex:1 1 auto; min-width:0; }
.db-brand { display:flex; align-items:center; gap:12px; }
.db-logo { width:42px; height:42px; border-radius:50%; padding:2px; background:linear-gradient(45deg,#0D7A5F,#98F4D3); flex:0 0 auto; }
.db-logo > span { display:block; width:100%; height:100%; border-radius:50%; border:2px solid var(--canvas);
  background:linear-gradient(45deg,#0A604B,#2BB58E 60%,#98F4D3); }
.db-title { font-size:22px; font-weight:700; letter-spacing:-0.015em; color:var(--text); white-space:nowrap; }
.db-icons { display:flex; align-items:center; gap:18px; color:#283044; }
.db-avatar { position:relative; width:38px; height:38px; border-radius:50%; background:var(--primary-soft);
  display:flex; align-items:center; justify-content:center; }
.db-avatar b { position:absolute; right:-3px; bottom:-3px; width:17px; height:17px; border-radius:50%; background:var(--primary);
  border:2px solid var(--canvas); color:#fff; font-size:9px; font-weight:700; display:flex; align-items:center; justify-content:center; }
.st-key-dtabs { gap:26px !important; border-bottom:1px solid var(--line); margin-top:4px; }
.db-tab { padding:10px 0 9px; font-size:15px; font-weight:500; color:var(--text-2); white-space:nowrap;
  border-bottom:2px solid transparent; margin-bottom:-1px; }
.db-tab.on { color:var(--text); font-weight:700; border-bottom-color:var(--text); }

/* Dashboard */
.db-card { background:#fff; border:1px solid var(--line); border-radius:18px; padding:20px 18px 14px; margin-top:16px; box-shadow:var(--shadow-1); }
.db-card-top { display:flex; justify-content:space-between; align-items:flex-start; }
.db-label { font-size:12px; font-weight:700; letter-spacing:0.08em; color:var(--text-2); }
.db-value { font-size:30px; font-weight:700; letter-spacing:-0.02em; color:var(--text); margin-top:8px; }
.db-round { display:flex; gap:8px; }
.db-round span { width:36px; height:36px; border-radius:50%; border:1px solid var(--line); display:flex; align-items:center;
  justify-content:center; color:#3E4944; }
.db-rows { border-top:1px dashed var(--chip-line); margin-top:16px; padding-top:6px; }
.db-row { display:flex; justify-content:space-between; align-items:center; padding:7px 0; font-size:14px; color:var(--text-2); }
.db-row b { font-weight:700; color:var(--text); }
.db-row b.up, .db-up { color:var(--primary) !important; }
.db-row .xirr { display:flex; align-items:center; gap:4px; }
.db-note { font-size:11px; color:#94A3B8; margin-top:6px; }
.db-sort { display:flex; justify-content:space-between; align-items:center; margin:22px 2px 6px; color:#283044; }
.db-sort span { display:flex; align-items:center; gap:6px; font-size:13px; font-weight:600; }
.db-sort u { text-decoration-style:dotted; text-underline-offset:4px; }
.db-fund { display:flex; justify-content:space-between; gap:16px; padding:10px 2px 16px; border-bottom:1px solid var(--line); }
.db-fund-name { font-size:15px; line-height:21px; color:var(--text); }
.db-tag { display:inline-block; margin-top:8px; padding:2px 8px; border-radius:6px; background:#E9EEF2; color:#475569;
  font-size:11px; font-weight:700; letter-spacing:0.03em; }
.db-fund-amt { text-align:right; white-space:nowrap; }
.db-fund-amt b { display:block; font-size:15px; color:var(--text); }
.db-fund-amt small { display:block; font-size:13px; font-weight:600; margin-top:6px; }
.db-import { display:flex; justify-content:center; margin:22px 0 6px; }
.db-import span { display:inline-flex; align-items:center; gap:10px; padding:10px 22px; border:1px solid var(--chip-line);
  border-radius:12px; font-size:14px; font-weight:500; color:var(--text); background:#fff; box-shadow:var(--shadow-1); }
.st-key-promo { margin-top:14px; border:1px solid var(--line); border-radius:18px; padding:22px 18px 22px 20px; background:#fff;
  box-shadow:var(--shadow-1); flex-wrap:nowrap !important; align-items:center; gap:8px !important; }
.st-key-promo > * { width:auto !important; }
.st-key-promo > *:first-child { flex:1 1 auto; min-width:0; }
.st-key-promo > *:last-child { flex:0 0 auto; }
.db-promo-t { font-size:16px; font-weight:700; line-height:23px; color:var(--text); }
.db-cal { position:relative; width:112px; height:112px; display:flex; align-items:center; justify-content:center; }
.db-cal i { position:absolute; color:#94A3B8; }
.st-key-start_sip button, .st-key-sheet_sip button { background:var(--primary); color:#fff; border:none; border-radius:10px;
  padding:8px 18px; min-height:0; }
.st-key-start_sip button p, .st-key-sheet_sip button p, .st-key-one_time button p { font-size:14px; font-weight:700; }
.st-key-start_sip button:hover, .st-key-sheet_sip button:hover { background:var(--primary-hover); color:#fff; }

/* Explore */
.ex-h { display:flex; justify-content:space-between; align-items:baseline; margin:22px 2px 12px; }
.ex-h b { font-size:18px; font-weight:700; color:var(--text); }
.ex-h small { font-size:11px; color:#94A3B8; }
.ex-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.ex-card { background:#fff; border:1px solid var(--line); border-radius:16px; padding:14px; box-shadow:var(--shadow-1);
  display:flex; flex-direction:column; min-height:148px; }
.ex-ico { width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center; }
.ex-name { flex:1; font-size:14px; font-weight:600; line-height:20px; color:var(--text); margin-top:12px; }
.ex-ret { display:flex; align-items:baseline; gap:6px; margin-top:10px; }
.ex-ret b { font-size:16px; font-weight:700; color:var(--primary); }
.ex-ret small { font-size:12px; font-weight:600; color:var(--text-2); }
.ex-coll { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
.ex-tile { background:#fff; border:1px solid var(--line); border-radius:16px; padding:16px 6px 14px; display:flex; flex-direction:column;
  align-items:center; gap:10px; text-align:center; font-size:13px; font-weight:600; line-height:17px; color:var(--text); }
.ex-tile span { width:44px; height:44px; border-radius:12px; background:var(--primary-soft); color:var(--primary);
  display:flex; align-items:center; justify-content:center; }

/* Bottom tab bar */
.db-nav { position:fixed; bottom:0; left:50%; transform:translateX(-50%); width:100%; max-width:512px; z-index:60;
  background:#fff; border-top:1px solid var(--line); display:flex; justify-content:space-around; padding:8px 0 10px; }
.db-nav span { flex:1; display:flex; flex-direction:column; align-items:center; gap:4px; font-size:11px; font-weight:500; color:var(--text-2); }
.db-nav span.on { color:var(--primary); font-weight:700; }

/* Profile */
.st-key-phdr { gap:16px !important; padding:16px 2px 4px; }
.st-key-phdr > *:nth-child(2) { margin-left:auto; }
.pf-ic { display:flex; color:#283044; padding:4px; }
.pf-pill { display:inline-flex; align-items:center; gap:6px; padding:6px 12px; border:1px solid var(--chip-line); border-radius:9999px;
  background:#fff; color:var(--primary); font-size:13px; font-weight:600; white-space:nowrap; }
.pf-top { display:flex; justify-content:space-between; align-items:flex-end; margin-top:18px; }
.pf-av { width:64px; height:64px; border-radius:50%; background:var(--primary-soft); color:var(--primary); font-size:22px;
  font-weight:700; display:flex; align-items:center; justify-content:center; border:2px solid #fff; box-shadow:var(--shadow-1); }
.pf-name { font-size:22px; font-weight:700; letter-spacing:-0.01em; color:var(--text); margin-top:12px; }
.pf-card { background:#fff; border:1px solid var(--line); border-radius:18px; margin-top:18px; box-shadow:var(--shadow-1); }
.pf-bal { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:14px 16px; border-bottom:1px solid var(--line); }
.pf-bal:last-child { border-bottom:none; }
.pf-bal small { display:block; font-size:13px; color:var(--text-2); }
.pf-bal b { display:block; font-size:16px; font-weight:700; color:var(--text); margin-top:2px; }
.pf-btn { padding:6px 14px; border-radius:9999px; background:var(--primary-soft); color:var(--primary); font-size:13px;
  font-weight:700; white-space:nowrap; }
.pf-list { margin-top:10px; }
.pf-link { display:flex; align-items:center; gap:14px; padding:15px 4px; border-bottom:1px solid var(--line);
  font-size:15px; font-weight:500; color:var(--text); }
.pf-link > span:first-child { display:flex; color:#3E4944; }
.pf-link > span:nth-child(2) { flex:1; }
.pf-link > span:last-child { display:flex; color:#94A3B8; }

/* Bottom sheet over a dimmed backdrop */
@keyframes db-up { from { transform:translate(-50%,100%); } to { transform:translate(-50%,0); } }
@keyframes db-fade { from { opacity:0; } to { opacity:1; } }
.st-key-sheet_close { position:fixed !important; inset:0; z-index:80; margin:0 !important; width:100vw !important; }
.st-key-sheet_close button, .st-key-sheet_close button:hover, .st-key-sheet_close button:focus, .st-key-sheet_close button:active {
  width:100vw; height:100vh; border:none; border-radius:0; background:rgba(15,23,42,.45); color:transparent; box-shadow:none; }
.st-key-sheet_close button { animation:db-fade .2s ease-out; }
.st-key-sheet { position:fixed !important; bottom:0; left:50%; transform:translate(-50%,0); width:100% !important; max-width:512px;
  z-index:90; background:#fff; border-radius:24px 24px 0 0; padding:10px 20px 24px; gap:0 !important;
  box-shadow:0 -8px 32px rgba(15,23,42,.18); animation:db-up .25s ease-out; }
.sh-grab { width:40px; height:4px; border-radius:2px; background:#CBD5E1; margin:0 auto 16px; }
.sh-fund { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; padding-bottom:14px;
  border-bottom:1px solid var(--line); }
.sh-fund-name { display:flex; align-items:center; gap:4px; font-size:16px; font-weight:700; line-height:22px; color:var(--text); }
.sh-fund-name svg { flex:0 0 auto; color:var(--text-2); }
.sh-fund-val { font-size:16px; font-weight:700; color:var(--text); white-space:nowrap; }
.sh-row { display:flex; align-items:center; gap:14px; padding:14px 2px; border-bottom:1px solid var(--line);
  font-size:15px; font-weight:600; color:var(--text); }
.sh-row > span:first-child { width:36px; height:36px; border-radius:50%; background:var(--primary-soft); color:var(--primary);
  display:flex; align-items:center; justify-content:center; }
.sh-row > span:nth-child(2) { flex:1; }
.sh-row > span:last-child { display:flex; color:#94A3B8; }
.st-key-sheet_btns { flex-wrap:nowrap !important; gap:12px !important; margin-top:20px; }
.st-key-sheet_btns > * { flex:1 1 0; width:auto !important; }
.st-key-sheet_btns button { width:100%; padding:12px; border-radius:12px; min-height:0; }
.st-key-one_time button { background:var(--primary-soft); border:1px solid var(--chip-line); color:var(--primary); }
.st-key-one_time button:hover { border-color:var(--primary); color:var(--primary); }
.sh-q { font-size:20px; font-weight:700; line-height:28px; letter-spacing:-0.01em; color:var(--text); margin:2px 0 16px; }
.sh-done { display:flex; flex-direction:column; align-items:center; text-align:center; padding:6px 4px 4px; }
.sh-done .sh-q { margin:12px 0 6px; }
.sh-sub { font-size:13px; line-height:19px; color:var(--text-2); margin-bottom:18px; }
.st-key-sheet_done button { background:var(--primary); color:#fff; border:none; border-radius:12px; padding:12px; min-height:0; }
.st-key-sheet_done button p { font-size:14px; font-weight:700; }
.st-key-sheet_done button:hover { background:var(--primary-hover); color:#fff; }
.st-key-reasons { flex-wrap:wrap !important; gap:10px !important; }
.st-key-reasons > * { width:auto !important; flex:0 0 auto; max-width:100%; }
.st-key-reasons button { border-radius:9999px; border:1px solid var(--chip-line); background:#fff; color:var(--text);
  padding:8px 14px; min-height:0; }
.st-key-reasons button p { font-size:13px; font-weight:600; white-space:normal; text-align:left; }
.st-key-reasons button:hover { border-color:var(--primary); color:var(--primary); }

@media (max-width: 400px) {
  .st-key-dtabs { gap:18px !important; } .st-key-dhdr { gap:12px !important; } .db-icons { gap:12px; }
  .db-value { font-size:26px; } .db-title { font-size:20px; }
}
</style>
"""


def _svg(paths: str, stroke: str = "currentColor", size: int = 20, width: float = 2) -> str:
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{stroke}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>')


def _html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def _tap(key: str, markup: str, label: str, on_click: Callable, args: tuple = ()) -> None:
    """Render `markup` with an invisible button over it, so the HTML itself is the tap target."""
    with st.container(key=f"tap_{key}"):
        _html(markup)
        st.button(label, key=f"tb_{key}", on_click=on_click, args=args)


# ---- Navigation callbacks --------------------------------------------------
def _go(view: str) -> None:
    if view == "profile":
        st.session_state.prev_view = st.session_state.view
    st.session_state.view = view
    st.session_state.sheet = None


def _back() -> None:
    _go(st.session_state.get("prev_view") or "dashboard")


def _open_sheet(sheet: str) -> None:
    st.session_state.sheet = sheet
    if sheet == "fund":
        st.session_state.exit_reason = None


def _close_sheet() -> None:
    st.session_state.sheet = None


def _pick_reason(i: int, open_chat: Callable[[str, list], None]) -> None:
    st.session_state.exit_reason = i
    if i in CHAT_BRIDGES:
        # Don't close: hand off to the chat. The sheet stays reachable via "Back to your SIP".
        st.session_state.sheet = None
        open_chat(*CHAT_BRIDGES[i])
    else:
        st.session_state.sheet = "closed"


def _noop() -> None:
    pass


# ---- Shared pieces -----------------------------------------------------------
def _header() -> None:
    with st.container(key="dhdr", horizontal=True):
        _html('<div class="db-brand"><div class="db-logo"><span></span></div><div class="db-title">Mutual Funds</div></div>')
        _html(f'<div class="db-icons">{_svg(SEARCH, size=22, width=2.2)}{_svg(LOADER, size=20)}</div>')
        _tap("avatar", f'<div class="db-avatar">{_svg(USER, "#0D7A5F", 20)}<b>₹</b></div>', "Open profile", _go, ("profile",))


def _tabs(active: str) -> None:
    with st.container(key="dtabs", horizontal=True):
        for name in ("Explore", "Dashboard", "SIPs", "Watchlist"):
            view = name.lower()
            markup = f'<div class="db-tab{" on" if view == active else ""}">{name}</div>'
            if view in VIEWS:
                _tap(f"tab_{view}", markup, f"{name} tab", _go, (view,))
            else:
                _html(markup)


def _bottom_nav() -> None:
    items = [("Stocks", STOCKS, False), ("F&amp;O", FNO, False), ("Mutual Funds", PIE, True), ("Loans", LOANS, False)]
    _html('<div class="db-nav">' + "".join(
        f'<span class="{"on" if on else ""}">{_svg(icon, size=22, width=1.8)}{label}</span>' for label, icon, on in items
    ) + '</div>')


# ---- Screens -------------------------------------------------------------------
def _explore() -> None:
    cards = "".join(
        f'<div class="ex-card"><div class="ex-ico" style="background:{tint};color:{ink}">{_svg(icon, size=20)}</div>'
        f'<div class="ex-name">{name}</div><div class="ex-ret"><b>{ret}</b><small>3Y</small></div></div>'
        for name, ret, icon, ink, tint in POPULAR
    )
    tiles = "".join(f'<div class="ex-tile"><span>{_svg(icon, size=22)}</span>{label}</div>' for label, icon in COLLECTIONS)
    _html(f'<div class="ex-h"><b>Popular Funds</b><small>{DEMO_NOTE}</small></div><div class="ex-grid">{cards}</div>'
          f'<div class="ex-h"><b>Collections</b></div><div class="ex-coll">{tiles}</div>')


def _dashboard(start_sip: Callable[[str], None]) -> None:
    h = HOLDINGS
    _html(
        '<div class="db-card"><div class="db-card-top"><div>'
        f'<div class="db-label">HOLDINGS ({h["count"]})</div><div class="db-value">{h["value"]}</div></div>'
        f'<div class="db-round"><span>{_svg(EYE, size=18)}</span><span>{_svg(BARS, size=18)}</span></div></div>'
        '<div class="db-rows">'
        f'<div class="db-row">1D returns<b class="up">{h["day"]}</b></div>'
        f'<div class="db-row">Total returns<b class="up">{h["total"]}</b></div>'
        f'<div class="db-row">Invested<b>{h["invested"]}</b></div>'
        f'<div class="db-row"><span class="xirr">XIRR{_svg(CHEV_DOWN, size=14)}</span><b>{h["xirr"]}</b></div>'
        f'</div><div class="db-note">{DEMO_NOTE}.</div></div>'
        f'<div class="db-sort">{_svg(FILTER, size=22)}<span>{_svg(SORT, "#64748B", 14)}<u>Day Change (%)</u></span></div>'
    )
    _tap("fund",
         f'<div class="db-fund"><div><div class="db-fund-name">{FUND_NAME}</div><span class="db-tag">SIP</span></div>'
         f'<div class="db-fund-amt"><b>{h["fund_day"]}</b><small class="db-up">{h["fund_day_pct"]}</small></div></div>',
         f"Open {FUND_NAME}", _open_sheet, ("fund",))
    _html(f'<div class="db-import"><span>{_svg(DOWNLOAD, size=18)}Import external funds</span></div>')

    with st.container(key="promo", horizontal=True):
        with st.container(key="promo_l", gap="medium"):
            _html('<div class="db-promo-t">Invest every month and grow your wealth with SIP</div>')
            st.button("Start a SIP", key="start_sip", on_click=start_sip, args=(START_SIP_QUESTION,))
        _html(f'<div class="db-cal"><i style="top:2px;right:46px">{_svg(SPARKLE, size=14, width=1)}</i>'
              f'<i style="top:10px;right:2px">{_svg(SPARKLE, size=10, width=1)}</i>{CALENDAR}</div>')


def _profile() -> None:
    with st.container(key="phdr", horizontal=True):
        _tap("back", f'<div class="pf-ic">{_svg(BACK, size=24)}</div>', "Back", _back)
        _html(f'<span class="pf-pill">{_svg(USER_PLUS, size=16)}Add family</span>')
        _html(f'<div class="pf-ic">{_svg(BELL, size=22)}</div>')
        _html(f'<div class="pf-ic">{_svg(GEAR, size=22)}</div>')
    balances = "".join(
        f'<div class="pf-bal"><div><small>{label}</small><b>{amount}</b></div><span class="pf-btn">{action}</span></div>'
        for label, amount, action in BALANCES
    )
    links = "".join(
        f'<div class="pf-link"><span>{_svg(icon, size=20)}</span><span>{label}</span><span>{_svg(CHEV_RIGHT, size=18)}</span></div>'
        for label, icon in PROFILE_LINKS
    )
    _html(f'<div class="pf-top"><div class="pf-av">{USER_INITIALS}</div>{SPARKLINE}</div>'
          f'<div class="pf-name">{USER_NAME}</div><div class="pf-card">{balances}</div><div class="pf-list">{links}</div>')


def _sheet(start_sip: Callable[[str], None], open_chat: Callable[[str, list], None]) -> None:
    def start(question: str) -> None:
        st.session_state.sheet = None
        start_sip(question)

    st.button("Close", key="sheet_close", on_click=_close_sheet)
    with st.container(key="sheet"):
        _html('<div class="sh-grab"></div>')
        if st.session_state.sheet == "fund":
            _html(f'<div class="sh-fund"><div><div class="sh-fund-name">{FUND_NAME}{_svg(CHEV_RIGHT, size=18)}</div>'
                  f'<span class="db-tag">SIP</span></div><div class="sh-fund-val">{HOLDINGS["value"]}</div></div>')
            _tap("redeem", f'<div class="sh-row"><span>{_svg(REDEEM, size=18)}</span><span>Redeem</span>'
                           f'<span>{_svg(CHEV_RIGHT, size=18)}</span></div>', "Redeem", _open_sheet, ("exit",))
            _html(f'<div class="sh-row"><span>{_svg(LIST, size=18)}</span><span>Investment details</span>'
                  f'<span>{_svg(CHEV_RIGHT, size=18)}</span></div>')
            with st.container(key="sheet_btns", horizontal=True):
                st.button("One Time", key="one_time", on_click=_noop)
                st.button("Start SIP", key="sheet_sip", on_click=start, args=(START_SIP_QUESTION,))
        elif st.session_state.sheet == "closed":
            # Simulated outcome only: holdings are untouched and nothing is sent anywhere.
            _html(f'<div class="sh-done">{_svg(CHECK, "#0D7A5F", 44)}'
                  '<div class="sh-q">Your SIP has been closed [demo]</div>'
                  f'<div class="sh-sub">Simulated for this demo — nothing was redeemed or changed. {FUND_NAME}.</div></div>')
            st.button("Done", key="sheet_done", on_click=_close_sheet, use_container_width=True)
        else:
            _html('<div class="sh-q">Before you go — can you tell us why?</div>')
            picked = st.session_state.get("exit_reason")
            if picked is not None:
                _html(f'<style>.st-key-reason_{picked} button {{ background:var(--primary-soft) !important; '
                      f'border-color:var(--primary) !important; color:var(--primary) !important; }}</style>')
            with st.container(key="reasons", horizontal=True):
                for i, reason in enumerate(EXIT_REASONS):
                    st.button(reason, key=f"reason_{i}", on_click=_pick_reason, args=(i, open_chat))


def render(start_sip: Callable[[str], None], open_chat: Callable[[str, list], None]) -> None:
    """Draw the current demo view.

    `start_sip(question)` opens the chat and asks `question`.
    `open_chat(opening_line, followups)` opens the chat with an assistant opening line.
    """
    st.session_state.setdefault("sheet", None)
    _html(CSS)
    view = st.session_state.view
    with st.container(key="screen"):
        if view == "profile":
            _profile()
        else:
            _header()
            _tabs(view)
            if view == "explore":
                _explore()
            else:
                _dashboard(start_sip)
            _bottom_nav()
    if view == "dashboard" and st.session_state.sheet:
        _sheet(start_sip, open_chat)
