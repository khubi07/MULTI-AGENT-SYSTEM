import time

import streamlit as st

from pipeline import run_research_pipeline

st.set_page_config(page_title="Relay", page_icon="🛰️", layout="wide")

STEPS = [
    ("Search", "Finds recent sources"),
    ("Read", "Scrapes the best one"),
    ("Write", "Drafts the report"),
    ("Critique", "Reviews the draft"),
]

EXAMPLES = [
    "Solid-state battery progress",
    "How RAG differs from fine-tuning",
    "State of open-source LLMs",
]

# ---------- styling ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Instrument+Sans:wght@400;500;600&display=swap');

:root {
  --bg: #13102A; --surface: #1D1941; --line: #342E66;
  --text: #ECE9FA; --muted: #A9A3D1;
  --violet: #8B6CFF; --amber: #FFB547; --mint: #5CE0B8; --rose: #FF6B8A;
}
html, body, .stApp, [class*="css"] { font-family: 'Instrument Sans', sans-serif; }
.stApp { background: radial-gradient(1200px 500px at 85% -10%, #2A2170 0%, var(--bg) 60%); }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 3.2rem; max-width: 1080px; }

h1.hero {
  font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800;
  font-size: clamp(2.2rem, 5vw, 3.6rem); line-height: 1.02; letter-spacing: -0.03em;
  margin: 0 0 .6rem 0; color: var(--text);
}
p.sub { color: var(--muted); font-size: 1.08rem; max-width: 56ch; margin: 0 0 1.8rem 0; }

/* input + buttons */
.stTextInput input {
  background: var(--surface) !important; color: var(--text) !important;
  border: 1.5px solid var(--line) !important; border-radius: 14px !important;
  padding: 0.95rem 1.1rem !important; font-size: 1.05rem !important;
}
.stTextInput input:focus { border-color: var(--violet) !important; box-shadow: 0 0 0 3px rgba(139,108,255,.25) !important; }
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
  border-radius: 12px; border: 1.5px solid var(--line); background: transparent;
  color: var(--text); font-weight: 600; transition: border-color .15s, background .15s;
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--violet); background: rgba(139,108,255,.12); color: var(--text); }
.stFormSubmitButton > button { background: var(--violet); border-color: var(--violet); color: #fff; padding: .7rem 1.4rem; }
.stFormSubmitButton > button:hover { background: #7A59F5; border-color: #7A59F5; color: #fff; }
[data-testid="stForm"] { border: none; padding: 0; background: transparent; }

/* relay */
.relay { position: relative; display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 1.6rem 0 1.2rem 0; }
.rail { position: absolute; top: -10px; left: 0; right: 0; height: 3px; background: var(--line); border-radius: 3px; overflow: hidden; }
.rail > i { display: block; height: 100%; background: linear-gradient(90deg, var(--violet), var(--mint)); transition: width .5s ease; }
.leg { background: var(--surface); border: 1.5px solid var(--line); border-radius: 16px; padding: 14px 16px; min-height: 92px; }
.leg b { font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.15rem; display: flex; align-items: center; gap: 9px; }
.leg span { display: block; color: var(--muted); font-size: .88rem; margin-top: 4px; }
.leg em { display: block; font-style: normal; font-size: .82rem; margin-top: 8px; color: var(--muted); font-variant-numeric: tabular-nums; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: var(--line); flex: none; }
.leg.running { border-color: var(--violet); box-shadow: 0 0 0 4px rgba(139,108,255,.15); }
.leg.running .dot { background: var(--violet); animation: pulse 1.1s ease-in-out infinite; }
.leg.done { border-color: rgba(92,224,184,.5); }
.leg.done .dot { background: var(--mint); }
.leg.error { border-color: var(--rose); }
.leg.error .dot { background: var(--rose); }
@keyframes pulse { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.7); opacity: .45; } }
@media (prefers-reduced-motion: reduce) { .leg.running .dot { animation: none; } .rail > i { transition: none; } }
@media (max-width: 760px) { .relay { grid-template-columns: 1fr 1fr; } }

/* results */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1.5px solid var(--line); }
.stTabs [data-baseweb="tab"] { color: var(--muted); font-weight: 600; padding: 10px 16px; }
.stTabs [aria-selected="true"] { color: var(--text); }
.stTabs [data-baseweb="tab-highlight"] { background: var(--violet); }
.report { background: var(--surface); border: 1.5px solid var(--line); border-radius: 18px; padding: 1.6rem 2rem; line-height: 1.7; max-width: 78ch; }
.critic { border-left: 4px solid var(--amber); background: rgba(255,181,71,.07); border-radius: 0 14px 14px 0; padding: 1.2rem 1.6rem; line-height: 1.65; }
.stat { color: var(--muted); font-size: .9rem; margin: .2rem 0 1rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- helpers ----------
def as_text(x) -> str:
    return str(getattr(x, "content", x))


def relay_html(states, times) -> str:
    done = sum(1 for s in states if s == "done")
    parts = [f'<div class="relay"><div class="rail"><i style="width:{done / len(STEPS) * 100:.0f}%"></i></div>']
    for (name, desc), state, t in zip(STEPS, states, times):
        note = {"pending": "Waiting", "running": "Working…", "error": "Failed"}.get(state, f"{t:.1f}s")
        parts.append(
            f'<div class="leg {state}"><b><span class="dot"></span>{name}</b>'
            f"<span>{desc}</span><em>{note}</em></div>"
        )
    parts.append("</div>")
    return "".join(parts)


def run_with_live_relay(topic: str, slot) -> dict:
    states = ["pending"] * len(STEPS)
    times = [0.0] * len(STEPS)
    slot.markdown(relay_html(states, times), unsafe_allow_html=True)

    started = time.perf_counter()
    states = ["running"] * len(STEPS)
    slot.markdown(relay_html(states, times), unsafe_allow_html=True)
    try:
        state = run_research_pipeline(topic)
    except Exception:
        states = ["error"] * len(STEPS)
        slot.markdown(relay_html(states, times), unsafe_allow_html=True)
        raise
    elapsed = time.perf_counter() - started
    states = ["done"] * len(STEPS)
    times = [elapsed / len(STEPS)] * len(STEPS)
    slot.markdown(relay_html(states, times), unsafe_allow_html=True)
    state["elapsed"] = elapsed
    return state


# ---------- page ----------
st.markdown('<h1 class="hero">Ask once.<br>Four agents take it from there.</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub">Relay searches the web, reads the best source, writes a report, '
    "and has a critic review it before you see it.</p>",
    unsafe_allow_html=True,
)

if "topic" not in st.session_state:
    st.session_state.topic = ""

with st.form("ask", border=False):
    c1, c2 = st.columns([5, 1.2], vertical_alignment="bottom")
    topic_in = c1.text_input(
        "Research topic",
        value=st.session_state.topic,
        placeholder="What do you want researched?",
        label_visibility="collapsed",
    )
    go = c2.form_submit_button("Run research", use_container_width=True)

chip_cols = st.columns(len(EXAMPLES) + 1)
for col, ex in zip(chip_cols, EXAMPLES):
    if col.button(ex, key=f"ex-{ex}", use_container_width=True):
        st.session_state.topic = ex
        st.rerun()

relay_slot = st.empty()

if go:
    topic = topic_in.strip()
    if not topic:
        st.warning("Enter a topic to research.")
    else:
        st.session_state.topic = topic
        try:
            st.session_state.result = run_with_live_relay(topic, relay_slot)
            st.session_state.result_topic = topic
        except Exception as e:
            st.session_state.pop("result", None)
            st.error(f"The pipeline stopped: {e}")
elif "result" in st.session_state:
    # redraw a finished relay on reruns (e.g. after clicking download)
    relay_slot.markdown(
        relay_html(["done"] * len(STEPS), [0.0] * len(STEPS)).replace("0.0s", "Done"),
        unsafe_allow_html=True,
    )

res = st.session_state.get("result")
if res:
    report = as_text(res["report"])
    st.markdown(
        f'<div class="stat">{len(report.split()):,} words · finished in {res.get("elapsed", 0):.0f}s</div>',
        unsafe_allow_html=True,
    )
    tab_report, tab_critic, tab_sources = st.tabs(["Report", "Critic feedback", "Sources"])

    with tab_report:
        with st.container(border=False):
            st.markdown(report)
        st.download_button(
            "Download report (.md)",
            report,
            file_name=f"{st.session_state.get('result_topic', 'report')[:40].strip().replace(' ', '_')}.md",
            mime="text/markdown",
        )

    with tab_critic:
        st.markdown(as_text(res["feedback"]))

    with tab_sources:
        with st.expander("Search results", expanded=False):
            st.markdown(as_text(res["search_result"]))
        with st.expander("Scraped content", expanded=False):
            st.markdown(as_text(res["reader_result"]))