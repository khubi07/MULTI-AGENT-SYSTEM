import streamlit as st
from pipeline import run_research_pipeline



st.set_page_config(
    page_title="Research Desk",
    page_icon="🔎",
    layout="wide",
)

st.markdown(
    """
    <style>
        .hero {
            padding: 1.5rem 0 1rem 0;
        }
        .eyebrow {
            color: #168c89;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 0.6rem;
        }
        .hero-copy {
            color: #667085;
            font-size: 1.05rem;
            max-width: 680px;
        }
    </style>

    <div class="hero">
        <div class="eyebrow">RESEARCH DESK</div>
        <h1>Make your next question a little clearer.</h1>
        <div class="hero-copy">
            Explore a topic and turn your findings into a structured, source-backed brief.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

with st.form("research_form"):
    topic = st.text_input(
        "What should we research?",
        placeholder="For example: How are cities adapting to extreme heat?"
    )

    submitted = st.form_submit_button(
        "Run research",
        type="primary",
        disabled=not topic.strip(),
    )

if submitted:
    st.session_state.pop("research_result", None)

    try:
        with st.status("Researching your topic…", expanded=True) as status:
            result = run_research_pipeline(topic.strip())

            status.update(
                label="Research complete",
                state="complete",
                expanded=False,
            )

        st.session_state["research_result"] = result

    except Exception as error:
        st.error("The research run failed. Check the terminal logs for details.")

        with st.expander("Technical error"):
            st.code(str(error))

result = st.session_state.get("research_result")

if result:
    st.divider()

    report_tab, research_tab, critique_tab = st.tabs(
        ["Research brief", "Research trail", "Critic review"]
    )

    with report_tab:
        st.markdown(result["report"])

    with research_tab:
        st.subheader("Search results")
        st.markdown(result["search_result"])

        st.subheader("Read source")
        st.markdown(result["reader_result"])

    with critique_tab:
        st.markdown(result["feedback"])