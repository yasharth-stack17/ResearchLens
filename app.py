"""ResearchLens: Streamlit front end. Run from the project root:  streamlit run app.py

Set RESEARCHLENS_PUBLIC=1 for public deployments: conversations then live only in the
visitor's session (in-memory) and nothing is written to disk.
"""
import html
import json
import os
import re
import sys
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # backend uses `from retrieve import ...`
os.chdir(ROOT)

st.set_page_config(page_title="ResearchLens", page_icon=":material/search:",
                   layout="centered", initial_sidebar_state="expanded")

PUBLIC = os.environ.get("RESEARCHLENS_PUBLIC", "").strip().lower() in ("1", "true", "yes")
N_PAPERS = 25

EXAMPLES = [
    ("What is NF4 and why does QLoRA use it?", False),
    ("What problem does FlashAttention solve, and how does it reduce memory traffic?", False),
    ("What is the key idea behind Direct Preference Optimization?", False),
    ("How do LoRA and QLoRA differ in memory use and base-model precision?", True),
]

# ------------------------------------------------------------------ theme
PALETTE = {
    "light": dict(bg="#F7F6F3", side="#EFEDE8", surface="#FFFFFF", raised="#EFEDE8", text="#24262B",
                  muted="#6C7078", line="#E0DDD5", accent="#4A55C8", accent_soft="rgba(74,85,200,.10)",
                  on_accent="#FFFFFF", warn="#8A5A00", warn_bg="rgba(191,135,0,.10)",
                  err="#B42318", err_bg="rgba(180,35,24,.07)", code="#EFEDE8"),
    "dark": dict(bg="#15171B", side="#1A1D22", surface="#1E2127", raised="#262A31", text="#E4E5E8",
                 muted="#979CA6", line="#2C3037", accent="#99A2F2", accent_soft="rgba(153,162,242,.14)",
                 on_accent="#15171B", warn="#E0B050", warn_bg="rgba(224,176,80,.10)",
                 err="#F0827A", err_bg="rgba(240,130,122,.09)", code="#23272E"),
}

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:wght@600&display=swap');
:root{--sans:Inter,-apple-system,"Segoe UI",Roboto,sans-serif;--serif:"Source Serif 4",Georgia,serif;}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:var(--bg)!important;color:var(--text);font-family:var(--sans);}
[data-testid="stHeader"]{background:transparent!important;}
[data-testid="stHeader"] *,[data-testid="stSidebarCollapseButton"] *,[data-testid="stExpandSidebarButton"] *{color:var(--muted)!important;}
[data-testid="stAppDeployButton"],footer{display:none!important;}
[data-testid="stBottom"],[data-testid="stBottom"]>div,[data-testid="stBottomBlockContainer"]{background:var(--bg)!important;}
[data-testid="stMainBlockContainer"],.block-container{max-width:46rem;padding:2rem 1.25rem 7rem;}
[data-testid="stSidebar"],[data-testid="stSidebar"]>div{background:var(--side)!important;}
[data-testid="stSidebar"]{border-right:1px solid var(--line);}
[data-testid="stSidebarUserContent"]{padding-top:1.2rem;}
hr,[data-testid="stDivider"] hr{border-color:var(--line)!important;}

/* text */
[data-testid="stMarkdownContainer"],[data-testid="stMarkdownContainer"] :is(p,li,h1,h2,h3,h4,strong,em,td,th){color:var(--text);}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] *{color:var(--muted)!important;}
[data-testid="stWidgetLabel"] *{color:var(--text)!important;}
[data-testid="stMarkdownContainer"] a{color:var(--accent);}
[data-testid="stMarkdownContainer"] code{background:var(--code);color:var(--text);border-radius:4px;padding:.1em .35em;font-size:.88em;}
[data-testid="stCode"] pre,[data-testid="stMarkdownContainer"] pre{background:var(--code)!important;border-radius:8px;}
[data-testid="stMarkdownContainer"] :is(th,td){border-color:var(--line)!important;}
[data-testid="stSpinner"] *{color:var(--muted)!important;}

/* chat */
[data-testid="stChatMessageAvatarUser"],[data-testid="stChatMessageAvatarAssistant"]{display:none;}
[data-testid="stChatMessage"]{background:transparent;padding:.55rem 0;gap:0;}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){background:var(--raised);border-radius:10px;padding:.7rem .95rem;margin-top:.8rem;}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] :is(p,li){font-size:.97rem;line-height:1.72;}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] :is(p,li) a[href*="arxiv.org/pdf/"]{display:inline-block;font-size:.7rem;font-weight:600;line-height:1.3;padding:.12rem .42rem;margin:0 .1rem;border-radius:5px;background:var(--accent-soft);color:var(--accent);text-decoration:none;vertical-align:.08em;}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] :is(p,li) a[href*="arxiv.org/pdf/"]:hover{text-decoration:underline;}

/* input */
[data-testid="stChatInput"],[data-testid="stChatInput"]>div,[data-testid="stChatInput"] textarea{background:var(--surface)!important;color:var(--text)!important;font-family:var(--sans);}
[data-testid="stChatInput"]{border:1px solid var(--line);border-radius:12px;}
[data-testid="stChatInput"]:focus-within{border-color:var(--accent);}
[data-testid="stChatInput"] textarea::placeholder{color:var(--muted)!important;opacity:1;}
[data-testid="stTextInput"] input,[data-baseweb="input"],[data-baseweb="base-input"]{background:var(--surface)!important;color:var(--text)!important;}
[data-testid="stTextInput"] [data-baseweb="input"]{border:1px solid var(--line);border-radius:8px;}

/* buttons */
[data-testid^="stBaseButton"]{font-family:var(--sans);border-radius:8px;height:auto;min-height:2.2rem;padding:.45rem .8rem;justify-content:flex-start;transition:background .12s,border-color .12s;}
[data-testid^="stBaseButton"] [data-testid="stMarkdownContainer"] p{white-space:normal;text-align:left;line-height:1.4;margin:0;font-size:.88rem;color:inherit;}
[data-testid^="stBaseButton"]:focus-visible{outline:2px solid var(--accent);outline-offset:1px;}
[data-testid="stBaseButton-secondary"]{background:var(--surface);border:1px solid var(--line);color:var(--text);}
[data-testid="stBaseButton-secondary"]:hover{border-color:var(--accent);color:var(--accent);}
[data-testid="stBaseButton-primary"]{background:var(--accent);border:1px solid var(--accent);color:var(--on-accent);}
[data-testid="stBaseButton-primary"] p{color:var(--on-accent);}
[data-testid="stBaseButton-tertiary"]{background:transparent;border:none;color:var(--text);}
[data-testid="stBaseButton-tertiary"]:hover{background:var(--raised);color:var(--text);}
.stButton,.stButton button{width:100%;}
.st-key-new_chat button{justify-content:center;}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]{background:var(--accent-soft);border:none;}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p{color:var(--text);font-weight:500;}
[data-testid="stSidebar"] [data-testid^="stBaseButton"] [data-testid="stMarkdownContainer"]{width:100%;min-width:0;overflow:hidden;}
[data-testid="stSidebar"] :is([data-testid="stBaseButton-tertiary"],[data-testid="stBaseButton-primary"]) p{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
[data-testid="stToggle"] label{gap:.5rem;}

/* popover + dialog (portals) */
[data-testid="stPopoverBody"],[data-baseweb="popover"]>div{background:var(--surface)!important;border:1px solid var(--line);}
[data-testid="stDialog"] div[role="dialog"]{background:var(--surface)!important;color:var(--text);border:1px solid var(--line);}
[data-testid="stDialog"] :is(h1,h2,h3){color:var(--text)!important;font-family:var(--sans);}
[data-testid="stDialog"] button svg{color:var(--muted);}

/* custom */
.rl-hero{margin:3.2rem 0 1.6rem;}
.rl-word{font-family:var(--serif);font-weight:600;font-size:2.7rem;letter-spacing:-.02em;line-height:1.1;color:var(--text);}
.rl-word b{color:var(--accent);font-weight:600;}
.rl-sbword{font-family:var(--serif);font-weight:600;font-size:1.3rem;letter-spacing:-.01em;margin-bottom:.9rem;color:var(--text);}
.rl-sbword b{color:var(--accent);font-weight:600;}
.rl-tag{font-size:1.05rem;line-height:1.6;color:var(--muted);margin:.8rem 0 0;max-width:34rem;}
.rl-label{font-size:.7rem;letter-spacing:.09em;text-transform:uppercase;font-weight:600;color:var(--muted);margin:1.1rem 0 .4rem;}
.rl-muted{font-size:.82rem;color:var(--muted);}
.rl-fine{font-size:.78rem;color:var(--muted);margin-top:1.2rem;line-height:1.5;}
.rl-title{font-size:1rem;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.rl-meta{font-size:.76rem;color:var(--muted);margin:.5rem 0 0;}
.rl-notice{border:1px solid var(--line);border-left-width:3px;border-radius:8px;padding:.75rem .95rem;font-size:.93rem;line-height:1.6;color:var(--text);}
.rl-notice b{display:block;margin-bottom:.15rem;}
.rl-notice small{display:block;color:var(--muted);margin-top:.4rem;font-size:.8rem;}
.rl-warn{border-left-color:var(--warn);background:var(--warn-bg);}
.rl-err{border-left-color:var(--err);background:var(--err-bg);}
.rl-src{border-top:1px solid var(--line);}
.rl-src:last-of-type{border-bottom:1px solid var(--line);}
.rl-src summary{cursor:pointer;display:flex;align-items:baseline;gap:.55rem;padding:.5rem .1rem;font-size:.86rem;list-style:none;color:var(--text);}
.rl-src summary::-webkit-details-marker{display:none;}
.rl-src summary:hover .rl-st{color:var(--accent);}
.rl-chip{flex:none;font-size:.68rem;font-weight:600;padding:.1rem .38rem;border-radius:5px;background:var(--accent-soft);color:var(--accent);}
.rl-st{flex:1;min-width:0;}
.rl-pg{flex:none;font-size:.76rem;color:var(--muted);}
.rl-sb{padding:.1rem .1rem .7rem 2.4rem;}
.rl-sl{font-size:.78rem;color:var(--muted);margin-bottom:.45rem;}
.rl-sl a{color:var(--accent);}
.rl-pass{font-size:.83rem;line-height:1.6;color:var(--text);background:var(--raised);border-radius:8px;padding:.6rem .75rem;word-break:break-word;}
@media(max-width:640px){[data-testid="stMainBlockContainer"],.block-container{padding:1.2rem .9rem 7rem;}.rl-word{font-size:2.2rem;}.rl-hero{margin-top:1.6rem;}.rl-sb{padding-left:.2rem;}}
"""


def inject_css(dark):
    p = PALETTE["dark" if dark else "light"]
    v = ";".join(f"--{k.replace('_', '-')}:{val}" for k, val in p.items())
    st.markdown(f"<style>:root{{{v};color-scheme:{'dark' if dark else 'light'}}}{BASE_CSS}</style>",
                unsafe_allow_html=True)


# ------------------------------------------------------------------ imports / backend / store
try:
    from generate import ask  # noqa: E402
    from history import SqliteStore, make_title  # noqa: E402
except Exception as e:  # pragma: no cover
    st.error("Could not import the backend. Run `streamlit run app.py` from the project root.")
    st.exception(e)
    st.stop()


@st.cache_resource(show_spinner="Loading retrieval models (first launch only)…")
def load_backend():
    from retrieve import Retriever
    from rerank import Reranker
    return Retriever(), Reranker()


@st.cache_resource
def _disk_store():
    return SqliteStore()


def get_store():
    if PUBLIC:  # per-session, in-memory: never shared between visitors, never written to disk
        if "mem_store" not in st.session_state:
            st.session_state["mem_store"] = SqliteStore(":memory:")
        return st.session_state["mem_store"]
    return _disk_store()


@st.cache_data(show_spinner=False)
def load_papers():
    try:
        meta = json.loads((ROOT / "data" / "meta.json").read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for m in meta.values():
        title = str(m.get("title", "")).strip()
        if title:
            out.append({"title": title, "year": str(m.get("year", "")), "category": str(m.get("category") or "Other"),
                        "arxiv_id": str(m.get("arxiv_id", "")), "pages": m.get("pages")})
    return sorted(out, key=lambda p: (p["category"], p["year"], p["title"]))


# ------------------------------------------------------------------ helpers
ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
CITE_RE = re.compile(r"\[(S\d+(?:\s*[,;]\s*S\d+)*)\]")
IMG_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\((?:[^()]|\([^)]*\))*\)")
REFDEF_RE = re.compile(r"^\s*\[[^\]]+\]:\s*\S+.*$", re.M)
SECRET_RE = re.compile(r"(gsk_[A-Za-z0-9]{8,}|AIza[0-9A-Za-z_\-]{20,}|Bearer\s+\S+)")


def esc(s):
    """HTML-escape; '$' becomes an entity so KaTeX never touches it."""
    return html.escape(str(s), quote=True).replace("$", "&#36;")


def flat(s):
    return re.sub(r"\s+", " ", str(s)).strip()


def redact(s):
    return SECRET_RE.sub("[redacted]", str(s))


def md_escape(s):
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|~$<>])", r"\\\1", flat(s))


def pdf_url(s):
    if ARXIV_RE.match(s["arxiv_id"] or "") and s["page"] and s["page"] >= 1:
        return f'https://arxiv.org/pdf/{s["arxiv_id"]}#page={s["page"]}'
    return None


def clean_sources(raw):
    out = []
    for s in raw or []:
        try:
            page = int(s.get("page"))
        except (TypeError, ValueError):
            page = None
        out.append({"id": str(s.get("id", "")), "title": str(s.get("title", "Untitled")),
                    "arxiv_id": str(s.get("arxiv_id", "")), "page": page, "text": str(s.get("text", ""))})
    return out


def render_answer(text, by_id):
    """Untrusted model text -> safe markdown. Links/images are stripped (Streamlit already refuses raw HTML);
    then ONLY validated [S#] ids become links, built from backend metadata."""
    text = REFDEF_RE.sub("", IMG_RE.sub(r"\1", text or ""))
    text = LINK_RE.sub(r"\1", text)

    def chip(sid):
        s = by_id.get(sid)
        u = pdf_url(s) if s else None
        if not u:
            return None
        tip = re.sub(r'["\[\]\\\n]', " ", f'{s["title"]} · p.{s["page"]}')
        return f'[{sid}]({u} "{tip}")'

    def repl(m):
        parts = [chip(i) for i in re.findall(r"S\d+", m.group(1))]
        return m.group(0) if any(p is None for p in parts) else "\u2009".join(parts)

    return CITE_RE.sub(repl, text)


def sources_html(sources):
    rows = []
    for s in sources:
        url = pdf_url(s)
        link = (f'<a href="{url}" target="_blank" rel="noopener noreferrer">Open PDF page ↗</a> · ' if url else "")
        pg = f'p.{s["page"]}' if s["page"] else ""
        rows.append(
            f'<details class="rl-src"><summary><span class="rl-chip">{esc(s["id"])}</span>'
            f'<span class="rl-st">{esc(s["title"])}</span><span class="rl-pg">{pg}</span></summary>'
            f'<div class="rl-sb"><div class="rl-sl">{link}arXiv:{esc(s["arxiv_id"])}</div>'
            f'<div class="rl-pass">{esc(flat(s["text"])) or "No passage text available."}</div></div></details>')
    return f'<div class="rl-label">Sources · {len(sources)}</div>' + "".join(rows)


def html_md(s):
    st.markdown(s, unsafe_allow_html=True)


# ------------------------------------------------------------------ state + callbacks
def set_active(cid):
    st.session_state.active = cid
    if cid:
        st.query_params["c"] = cid
    elif "c" in st.query_params:
        del st.query_params["c"]


def new_chat():
    set_active(None)


def open_conv(cid):
    set_active(cid)


def use_example(q, comp):
    st.session_state.pending = q
    st.session_state.compare = comp


def retry(user_id, asst_id, q, comp):
    store = get_store()
    if asst_id:
        store.delete_message(asst_id)
    store.delete_message(user_id)
    st.session_state.pending = q
    st.session_state.compare = comp


def save_theme():
    get_store().set_setting("theme", "dark" if st.session_state.dark_mode else "light")


# ------------------------------------------------------------------ dialogs
@st.dialog("Rename conversation")
def rename_dialog(cid, current):
    new = st.text_input("Title", value=current, max_chars=80)
    if st.button("Save", type="primary") and new.strip():
        get_store().rename(cid, new)
        st.rerun()


@st.dialog("Delete conversation")
def delete_dialog(cid, title):
    st.write(f"Delete “{flat(title)}”? This can’t be undone.")
    c1, c2 = st.columns(2)
    if c1.button("Delete", type="primary", key="del_ok"):
        get_store().delete_conversation(cid)
        set_active(None)
        st.rerun()
    if c2.button("Cancel", key="del_cancel"):
        st.rerun()


@st.dialog("Paper library", width="large")
def library_dialog():
    papers = load_papers()
    if not papers:
        st.info("data/meta.json could not be read.")
        return
    q = st.text_input("Search", placeholder="Search title, category, year or arXiv ID",
                      label_visibility="collapsed").lower().strip()
    shown = [p for p in papers if not q or q in f'{p["title"]} {p["category"]} {p["year"]} {p["arxiv_id"]}'.lower()]
    st.caption(f"{len(shown)} of {len(papers)} papers")
    cat = None
    for p in shown:
        if p["category"] != cat:
            cat = p["category"]
            st.markdown(f"**{md_escape(cat)}**")
        t = md_escape(p["title"])
        line = f"[{t}](https://arxiv.org/abs/{p['arxiv_id']})" if ARXIV_RE.match(p["arxiv_id"]) else t
        st.markdown(f"- {line} · {md_escape(p['year'])}" + (f" · {p['pages']} pp." if p["pages"] else ""))


@st.dialog("About ResearchLens", width="large")
def about_dialog():
    st.markdown(
        "ResearchLens answers questions about a **fixed set of 25 influential AI/ML papers** (679 PDF pages, "
        "3,212 text chunks) and cites the paper and PDF page behind each claim. If the retrieved passages don’t "
        "support an answer, it says so instead of guessing.\n\n"
        "**How it works**\n"
        "1. **Hybrid retrieval:** BM25 and BGE-small dense search (FAISS), merged with reciprocal rank fusion.\n"
        "2. **Reranking:** a MiniLM cross-encoder re-scores the top 30 candidates; the best 5 are kept.\n"
        "3. **Grounded generation:** `openai/gpt-oss-120b` (via Groq) answers using only the labelled passages, "
        "citing them as `[S#]`. Citations are checked against the passages actually returned.\n"
        "4. **Compare papers (optional):** keeps at most two passages per paper so each paper in an “X vs Y” question "
        "is represented. It is never switched on automatically.\n\n"
        "**Measured on our 50-question benchmark** (`eval/results/`)\n\n"
        "| System | Recall@5 | Comparison Cov@5 | Comparison Full@5 |\n|---|---:|---:|---:|\n"
        "| BM25 | 0.667 | 0.744 | 0.467 |\n| Dense | 0.700 | 0.844 | 0.667 |\n| Hybrid | 0.667 | 0.811 | 0.600 |\n"
        "| Hybrid + Rerank | 0.733 | 0.811 | 0.600 |\n| Hybrid + Diversify | 0.367 | 1.000 | 1.000 |\n"
        "| Hybrid + Rerank + Diversify | 0.433 | 0.944 | 0.867 |\n\n"
        "Recall@5 covers the 30 single-paper and definition questions (correct paper **and** a gold page). Comparison "
        "metrics cover the 15 cross-paper questions. Diversification improves paper coverage but sharply lowers "
        "page-level precision, which is why Compare papers is opt-in. Paper coverage does not guarantee the exact "
        "evidence pages were retrieved.\n\n"
        "In generation tests the system declined all 5 unanswerable benchmark questions. That is a small sample: "
        "answer faithfulness and the false-abstention rate have not been measured.\n\n"
        "**Limitations**\n"
        "- Each question is answered independently. Saved history is for reading and resuming; follow-ups such as "
        "“and what about QLoRA?” don’t see earlier messages.\n"
        "- Fixed corpus; no uploads. Answers are LLM-generated, so verify against the linked page.\n"
        "- Page links open the latest arXiv version, whose pagination may differ from the indexed PDF.")


@st.dialog("Settings")
def settings_dialog():
    store = get_store()
    n = len(store.list_conversations(100000))
    if PUBLIC:
        st.write("Session-only mode: conversations are kept in memory for this visit and are never written to disk.")
    else:
        st.write(f"**{n}** saved conversation{'s' if n != 1 else ''}, stored locally in `data/chat_history.sqlite3`.")
    st.caption("Chat history is stored on this machine only and is not authenticated; it is intended for local, "
               "single-user use.")
    ok = st.checkbox("I understand this permanently deletes all conversations", key="wipe_ok")
    if st.button("Delete all conversations", disabled=not ok, type="primary", key="wipe_btn"):
        store.delete_all()
        set_active(None)
        st.session_state.wipe_ok = False
        st.rerun()


# ------------------------------------------------------------------ rendering
def render_assistant(m, prev, last):
    r = m.get("result") or {}
    sources = clean_sources(r.get("sources"))
    by_id = {s["id"]: s for s in sources}

    if r.get("error"):
        low = redact(r["error"]).lower()
        hint = ("Check that GROQ_API_KEY is set in the project’s .env file, then restart the app." if "key" in low else
                "The LLM provider is rate-limiting requests. Wait a moment and retry." if ("rate" in low or "429" in low) else
                "Please try again. If it persists, check the terminal running Streamlit.")
        html_md(f'<div class="rl-notice rl-err"><b>Couldn’t produce an answer</b>{esc(flat(redact(r["error"])))}'
                f'<small>{esc(hint)}</small></div>')
        if last and prev:
            st.button("Retry", key=f"retry_{m['id']}", icon=":material/refresh:", on_click=retry,
                      args=(prev["id"], m["id"], prev["content"], prev["comparison"]))
        return
    if r.get("abstained"):
        html_md(f'<div class="rl-notice rl-warn"><b>Not answered</b>{esc(flat(r.get("answer", "")))}'
                f'<small>ResearchLens answers only when the indexed papers support it.</small></div>')
    else:
        st.markdown(render_answer(r.get("answer", ""), by_id))
    if sources:
        html_md(sources_html(sources))
    bits = ["Compare papers" if m.get("comparison") else "Standard retrieval"]
    if m.get("elapsed"):
        bits.append(f'{m["elapsed"]:.1f} s')
    html_md(f'<div class="rl-meta">{" · ".join(bits)}</div>')


def sidebar(store, active):
    with st.sidebar:
        html_md('<div class="rl-sbword">Research<b>Lens</b></div>')
        st.button("New conversation", key="new_chat", icon=":material/add:", on_click=new_chat)
        html_md('<div class="rl-label">Recent</div>')
        convs = store.list_conversations(30)
        if not convs:
            html_md('<div class="rl-muted">No conversations yet.</div>')
        for c in convs:
            st.button(md_escape(c["title"]) or "Untitled", key=f"conv_{c['id']}",
                      type="primary" if c["id"] == active else "tertiary", on_click=open_conv, args=(c["id"],))
        if PUBLIC:
            html_md('<div class="rl-fine">Session-only: conversations aren’t saved after you leave.</div>')
        st.divider()
        if st.button("Paper library", key="b_lib", type="tertiary", icon=":material/menu_book:"):
            library_dialog()
        if st.button("About & methodology", key="b_about", type="tertiary", icon=":material/info:"):
            about_dialog()
        if st.button("Settings", key="b_set", type="tertiary", icon=":material/settings:"):
            settings_dialog()
        st.toggle("Dark mode", key="dark_mode", on_change=save_theme)


# ------------------------------------------------------------------ page
store = get_store()
ss = st.session_state
if "dark_mode" not in ss:
    ss.dark_mode = store.get_setting("theme", "light") == "dark"
ss.setdefault("compare", False)
if "active" not in ss:
    cid = st.query_params.get("c")
    ss.active = cid if cid and store.get_conversation(cid) else None
if ss.active and not store.get_conversation(ss.active):
    set_active(None)

inject_css(ss.dark_mode)

typed = st.chat_input("Ask a self-contained question about the papers…")
question = (typed or ss.pop("pending", None) or "").strip()

run_q = None
if question:
    comp = bool(ss.compare)
    if ss.active is None:
        set_active(store.create_conversation(make_title(question)))
    uid = store.add_message(ss.active, "user", question, comp)
    run_q = (question, comp, uid)

active = ss.active
conv = store.get_conversation(active) if active else None
sidebar(store, active)

# top row: title + options | compare toggle
left, mid, right = st.columns([6, 1, 4], vertical_alignment="center")
with left:
    if conv:
        html_md(f'<div class="rl-title">{esc(conv["title"])}</div>')
with mid:
    if conv:
        with st.popover("⋯", help="Conversation options"):
            if st.button("Rename", key="opt_rename", type="tertiary", icon=":material/edit:"):
                rename_dialog(conv["id"], conv["title"])
            if st.button("Delete", key="opt_delete", type="tertiary", icon=":material/delete:"):
                delete_dialog(conv["id"], conv["title"])
with right:
    st.toggle("Compare papers", key="compare",
              help="Retrieves up to two passages per paper so each paper in an “X vs Y” question is represented. "
                   "Can lower page-level precision on single-paper questions. Off by default; never automatic.")

try:
    retriever, reranker = load_backend()
except Exception as e:
    st.error("Could not load the retrieval backend. Check that data/index/ exists and that you launched the app "
             "from the project root.")
    with st.expander("Details"):
        st.exception(e)
    st.stop()

msgs = store.get_messages(active) if active else []

if not msgs:
    html_md('<div class="rl-hero"><div class="rl-word">Research<b>Lens</b></div>'
            f'<p class="rl-tag">Ask a question about {N_PAPERS} influential AI/ML papers. Answers cite the paper and '
            'page, or say the papers don’t cover it.</p></div>')
    html_md('<div class="rl-label">Try asking</div>')
    for i, (q, c) in enumerate(EXAMPLES):
        st.button(q, key=f"ex{i}", on_click=use_example, args=(q, c),
                  icon=":material/compare_arrows:" if c else None,
                  help="Turns on Compare papers" if c else None)
    html_md('<div class="rl-fine">Each question is answered on its own, so make it self-contained. '
            'Answers are generated by an LLM from retrieved passages; check the linked page.</div>')

prev = None
for i, m in enumerate(msgs):
    if m["role"] == "user":
        with st.chat_message("user"):
            st.markdown(m["content"])
        prev = m
    else:
        with st.chat_message("assistant"):
            render_assistant(m, prev, last=(i == len(msgs) - 1))

if msgs and msgs[-1]["role"] == "user" and not run_q:  # interrupted run: question saved, no answer
    with st.chat_message("assistant"):
        html_md('<div class="rl-notice rl-err"><b>No answer was saved</b>The run was interrupted before an answer '
                'came back.</div>')
        u = msgs[-1]
        st.button("Retry", key=f"retry_u{u['id']}", icon=":material/refresh:", on_click=retry,
                  args=(u["id"], None, u["content"], u["comparison"]))

if run_q:
    q, comp, uid = run_q
    with st.chat_message("assistant"):
        with st.spinner("Searching the papers and drafting a cited answer…"):
            t0 = time.perf_counter()
            try:
                result = ask(q, comparison=comp, retriever=retriever, reranker=reranker)
            except Exception as e:  # backend returns errors in the dict, but never crash the UI
                result = {"answer": "", "sources": [], "abstained": False,
                          "error": f"Unexpected {type(e).__name__}: {redact(e)}"}
            elapsed = time.perf_counter() - t0
        if not isinstance(result, dict):
            result = {"answer": "", "sources": [], "abstained": False,
                      "error": "The backend returned an unexpected response."}
        mid_ = store.add_message(active, "assistant", "", comp, result, elapsed)
        render_assistant({"id": mid_, "result": result, "comparison": comp, "elapsed": elapsed},
                         {"id": uid, "content": q, "comparison": comp}, last=True)