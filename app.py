"""
Streamlit UI for the Multi-Agent Research System (Search -> Scrape -> Write -> Critique).

Run from the project root (same folder as Agent.py, pipeline.py, tool.py):
    streamlit run app.py
"""

import re
from datetime import datetime

import streamlit as st

try:
    from pipeline import research_pipeline
except Exception as e:
    st.set_page_config(page_title="Research Console", page_icon="🛰️")
    st.error(
        "Couldn't import `research_pipeline` from pipeline.py.\n\n"
        f"Details: {e}\n\n"
        "Make sure app.py sits in the same folder as Agent.py, pipeline.py and tool.py, "
        "and that all pipeline dependencies are installed."
    )
    st.stop()


# ----------------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Research Console",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

STAGES = [
    ("01", "SEARCH", "Search Agent"),
    ("02", "SCRAPE", "Scraper Agent"),
    ("03", "WRITE", "Writer"),
    ("04", "CRITIQUE", "Critic"),
]

STAGE_EVENTS = {
    "Starting Search Agent...": (0, "active"),
    "Search Agent finished.": (0, "done"),
    "Starting Scraper Agent...": (1, "active"),
    "Scraper Agent finished.": (1, "done"),
    "Writing report...": (2, "active"),
    "Report drafted.": (2, "done"),
    "Running critic review...": (3, "active"),
    "Critic review complete.": (3, "done"),
}

EXAMPLE_TOPICS = [
    "Latest developments in AI",
    "Renewable energy breakthroughs 2026",
    "Global semiconductor supply chain",
]


# ----------------------------------------------------------------------------
# Styling — dark "research console" shell with a light "dossier page" for the report
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

    :root {
        --ink: #0D1321;
        --panel: #161B2E;
        --panel-border: #262E47;
        --text: #E7E9F0;
        --muted: #8891A8;
        --amber: #E8A33D;
        --teal: #45D6B0;
        --rose: #E5646B;
        --paper: #F6F2E8;
        --paper-ink: #1D1B16;
    }

    .stApp { background: var(--ink); }
    .stApp, .stApp p, .stApp label, .stApp span { color: var(--text); font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Fraunces', serif !important; }

    [data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--panel-border); }
    [data-testid="stSidebar"] * { color: var(--text) !important; }

    .console-title { font-family: 'Fraunces', serif; font-size: 2.3rem; font-weight: 700; margin-bottom: 0.1rem; }
    .console-sub { color: var(--muted); font-size: 1rem; margin-top: 0; }
    .gradient-rule { height: 3px; width: 100%; margin: 1.1rem 0 1.8rem 0; border-radius: 2px;
        background: linear-gradient(90deg, var(--amber), var(--teal)); }

    .stButton>button {
        background: var(--amber); color: #1D1305; border: none; border-radius: 8px;
        font-weight: 600; font-family: 'Inter', sans-serif; transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stButton>button:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(232,163,61,0.35); }
    button[kind="secondary"] {
        background: transparent !important; border: 1px solid var(--panel-border) !important;
        color: var(--muted) !important; font-family: 'IBM Plex Mono', monospace !important;
        font-size: 0.75rem !important; border-radius: 20px !important;
    }

    [data-testid="stTextInput"] input {
        background: var(--panel); border: 1px solid var(--panel-border); color: var(--text);
        border-radius: 8px; font-family: 'Inter', sans-serif;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--panel-border); }
    .stTabs [data-baseweb="tab"] { font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; letter-spacing: 0.04em; color: var(--muted); }
    .stTabs [aria-selected="true"] { color: var(--amber) !important; }

    .tracker { display: flex; flex-wrap: wrap; border: 1px solid var(--panel-border); border-radius: 10px; overflow: hidden; margin-bottom: 1.4rem; }
    .stage { flex: 1 1 200px; position: relative; display: flex; align-items: center; gap: 12px;
        padding: 14px 18px; background: var(--panel); border-right: 1px solid var(--panel-border); }
    .stage:last-child { border-right: none; }
    .stage-num { font-family: 'Fraunces', serif; font-size: 1.5rem; font-weight: 600; color: var(--muted); }
    .stage-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; letter-spacing: 0.08em; color: var(--muted); }
    .stage-name { font-size: 0.95rem; color: var(--text); font-weight: 500; }
    .stage-dot { position: absolute; top: 12px; right: 14px; width: 8px; height: 8px; border-radius: 50%;
        background: var(--panel-border); transition: background 0.3s ease, box-shadow 0.3s ease; }
    .stage-active .stage-dot { background: var(--amber); box-shadow: 0 0 8px var(--amber); }
    .stage-active .stage-num { color: var(--amber); }
    .stage-done .stage-dot { background: var(--teal); box-shadow: 0 0 8px var(--teal); }
    .stage-done .stage-num { color: var(--teal); }
    .stage-error .stage-dot { background: var(--rose); box-shadow: 0 0 8px var(--rose); }

    .log-panel { background: var(--ink); border: 1px solid var(--panel-border); border-radius: 8px;
        padding: 12px 16px; font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; color: var(--muted);
        max-height: 190px; overflow-y: auto; margin-bottom: 1.4rem; }
    .log-line { padding: 2px 0; }
    .log-caret { color: var(--amber); margin-right: 8px; }

    .report-paper { background: var(--paper); color: var(--paper-ink); border-radius: 6px;
        padding: 2.2rem 2.4rem; font-family: 'Inter', sans-serif; line-height: 1.65;
        box-shadow: 0 12px 30px rgba(0,0,0,0.35); }
    .report-paper h1, .report-paper h2, .report-paper h3 { font-family: 'Fraunces', serif; color: var(--paper-ink); }
    .report-paper p, .report-paper li, .report-paper span { color: var(--paper-ink) !important; }

    .raw-panel { background: var(--panel); border: 1px solid var(--panel-border); border-radius: 8px;
        padding: 1.4rem 1.6rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem;
        color: var(--text); white-space: pre-wrap; line-height: 1.6; max-height: 520px; overflow-y: auto; }

    .critic-panel { background: var(--panel); border-left: 3px solid var(--rose); border-radius: 0 8px 8px 0;
        padding: 1.4rem 1.6rem; font-family: 'Inter', sans-serif; color: var(--text); line-height: 1.65; }

    .footnote { color: var(--muted); font-size: 0.78rem; margin-top: 2.5rem; font-family: 'IBM Plex Mono', monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def as_text(value) -> str:
    """Normalize chain/agent output to plain text, whether it's a str or a message-like object."""
    if isinstance(value, str):
        return value
    return getattr(value, "content", str(value))


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return slug[:50] or "report"


def render_tracker(statuses) -> str:
    cells = []
    for (num, label, name), status in zip(STAGES, statuses):
        cells.append(
            f'<div class="stage stage-{status}">'
            f'<div class="stage-num">{num}</div>'
            f'<div class="stage-body">'
            f'<div class="stage-label">{label}</div>'
            f'<div class="stage-name">{name}</div>'
            f"</div>"
            f'<div class="stage-dot"></div>'
            f"</div>"
        )
    return f'<div class="tracker">{"".join(cells)}</div>'


def render_log(lines) -> str:
    rows = "".join(f'<div class="log-line"><span class="log-caret">›</span>{line}</div>' for line in lines)
    return f'<div class="log-panel">{rows}</div>'


# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
if "topic_input" not in st.session_state:
    st.session_state.topic_input = ""
if "result" not in st.session_state:
    st.session_state.result = None
if "result_topic" not in st.session_state:
    st.session_state.result_topic = ""
if "final_statuses" not in st.session_state:
    st.session_state.final_statuses = ["pending"] * 4
if "history" not in st.session_state:
    st.session_state.history = []


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛰️ RESEARCH CONSOLE")
    st.caption("Multi-agent research pipeline")

    with st.expander("How it works", expanded=False):
        for num, label, name in STAGES:
            st.markdown(f"**{num} · {label}** — {name}")
        st.caption("Search finds sources → Scraper pulls deeper content → Writer drafts the report → Critic reviews it.")

    st.divider()
    st.markdown("**Session log**")
    if st.session_state.history:
        for past_topic in st.session_state.history[:10]:
            if st.button(past_topic, key=f"hist_{past_topic}", use_container_width=True, type="secondary"):
                st.session_state.topic_input = past_topic
                st.rerun()
    else:
        st.caption("No runs yet this session.")


# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.markdown('<div class="console-title">Multi-Agent Research Console</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="console-sub">Search → Scrape → Write → Critique, orchestrated end-to-end.</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="gradient-rule"></div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Input row
# ----------------------------------------------------------------------------
input_col, button_col = st.columns([4, 1])
with input_col:
    st.text_input(
        "Research topic",
        key="topic_input",
        placeholder="e.g. Latest developments in AI",
        label_visibility="collapsed",
    )
with button_col:
    run_clicked = st.button("▶ Run Pipeline", use_container_width=True, type="primary")

chip_cols = st.columns(len(EXAMPLE_TOPICS))
for i, example in enumerate(EXAMPLE_TOPICS):
    if chip_cols[i].button(example, key=f"chip_{i}", use_container_width=True, type="secondary"):
        st.session_state.topic_input = example
        st.rerun()

st.write("")


# ----------------------------------------------------------------------------
# Run pipeline with live progress
# ----------------------------------------------------------------------------
if run_clicked:
    topic = st.session_state.topic_input.strip()
    if not topic:
        st.warning("Enter a topic to research first.")
    else:
        statuses = ["pending"] * 4
        log_lines = []

        tracker_ph = st.empty()
        log_ph = st.empty()
        tracker_ph.markdown(render_tracker(statuses), unsafe_allow_html=True)

        def on_progress(message: str):
            if message in STAGE_EVENTS:
                idx, status = STAGE_EVENTS[message]
                statuses[idx] = status
            log_lines.append(message)
            tracker_ph.markdown(render_tracker(statuses), unsafe_allow_html=True)
            log_ph.markdown(render_log(log_lines), unsafe_allow_html=True)

        try:
            with st.spinner("Agents are working..."):
                result = research_pipeline(topic, status_callback=on_progress)
            st.session_state.result = result
            st.session_state.result_topic = topic
            st.session_state.final_statuses = statuses
            st.session_state.history.insert(0, topic)
            st.success(f"Pipeline complete for: {topic}")
        except Exception as e:
            for i, s in enumerate(statuses):
                if s == "active":
                    statuses[i] = "error"
            tracker_ph.markdown(render_tracker(statuses), unsafe_allow_html=True)
            st.error(f"Pipeline failed: {e}")


# ----------------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------------
if st.session_state.result:
    result = st.session_state.result
    topic = st.session_state.result_topic

    if not run_clicked:
        st.markdown(render_tracker(st.session_state.final_statuses), unsafe_allow_html=True)

    report_text = as_text(result.get("Report", "No report generated."))
    search_text = as_text(result.get("Search Response", "No search response found."))
    scraped_text = as_text(result.get("Scraped Response", "No scraped response found."))
    feedback_text = as_text(result.get("Feedback", "No feedback generated."))

    tab_report, tab_search, tab_scraped, tab_critic = st.tabs(
        ["📰 REPORT", "🔎 SEARCH LOG", "🌐 SCRAPED SOURCE", "🧭 CRITIC NOTES"]
    )

    with tab_report:
        st.markdown(f'<div class="report-paper">{report_text}</div>', unsafe_allow_html=True)
        st.download_button(
            "⬇ Download report (.md)",
            data=report_text,
            file_name=f"{slugify(topic)}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
        )

    with tab_search:
        st.markdown(f'<div class="raw-panel">{search_text}</div>', unsafe_allow_html=True)

    with tab_scraped:
        st.markdown(f'<div class="raw-panel">{scraped_text}</div>', unsafe_allow_html=True)

    with tab_critic:
        st.markdown(f'<div class="critic-panel">{feedback_text}</div>', unsafe_allow_html=True)

st.markdown(
    f'<div class="footnote">Search Agent · Scraper Agent · Writer · Critic — '
    f'session started {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>',
    unsafe_allow_html=True,
)