
"""
app.py — Tractian RAG Demo (Streamlit)

Run:
    pip install google-genai chromadb streamlit sentence-transformers
    streamlit run app.py
"""

import os
import streamlit as st
from rag_engine import ingest_manual, ingest_log, query

st.set_page_config(
    page_title="Tractian Maintenance Assistant",
    page_icon="🔧",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

    .stApp { background-color: #0a0e1a; color: #cdd6f4; font-family: 'IBM Plex Sans', sans-serif; }
    .block-container { padding: 2rem 2.5rem; }

    h1 { color: #89b4fa; font-family: 'IBM Plex Mono', monospace; font-size: 1.4rem; letter-spacing: 0.02em; }
    h2, h3 { color: #89dceb; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.08em; }

    /* confidence badge */
    .badge {
        display: inline-block; border-radius: 4px;
        padding: 3px 10px; font-size: 0.75rem;
        font-family: 'IBM Plex Mono', monospace; font-weight: 600; letter-spacing: 0.05em;
    }
    .badge-high   { background: #1e3a2f; color: #a6e3a1; border: 1px solid #a6e3a1; }
    .badge-medium { background: #3a2e1a; color: #f9e2af; border: 1px solid #f9e2af; }
    .badge-low    { background: #3a1a1a; color: #f38ba8; border: 1px solid #f38ba8; }

    /* cards */
    .card {
        background: #131825; border: 1px solid #1e2d45;
        border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 0.6rem;
    }
    .card-warn {
        background: #2a1a0a; border: 1px solid #f9e2af;
        border-radius: 8px; padding: 0.8rem 1.2rem; margin-bottom: 0.6rem;
        color: #f9e2af;
    }
    .card-alert {
        background: #2a0a0a; border: 1px solid #f38ba8;
        border-radius: 8px; padding: 0.8rem 1.2rem; margin-bottom: 0.6rem;
        color: #f38ba8;
    }
    .card-pattern {
        background: #1a1a2a; border: 1px solid #cba6f7;
        border-radius: 8px; padding: 0.8rem 1.2rem; margin-bottom: 0.6rem;
        color: #cba6f7;
    }

    /* source pill */
    .pill {
        display: inline-block; background: #1e2d45;
        border-radius: 3px; padding: 1px 7px;
        font-size: 0.7rem; font-family: 'IBM Plex Mono', monospace;
        color: #89dceb; margin-left: 6px;
    }

    /* step/cause rows */
    .item-row {
        padding: 0.5rem 0; border-bottom: 1px solid #1e2d45;
        display: flex; align-items: flex-start; gap: 0.5rem;
    }
    .item-num {
        font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;
        color: #6c7086; min-width: 1.5rem; padding-top: 2px;
    }
    .item-text { flex: 1; font-size: 0.92rem; line-height: 1.5; }

    /* summary box */
    .summary-box {
        background: #131825; border-left: 3px solid #89b4fa;
        padding: 0.8rem 1.2rem; border-radius: 0 8px 8px 0;
        font-size: 1rem; line-height: 1.6; margin-bottom: 1rem;
    }

    /* incident card */
    .incident {
        background: #0f1520; border: 1px solid #1e2d45;
        border-radius: 6px; padding: 0.6rem 0.9rem; margin-bottom: 0.4rem;
    }
    .incident-id { font-family: 'IBM Plex Mono', monospace; color: #89b4fa; font-size: 0.8rem; }
    .incident-res { font-size: 0.85rem; color: #a6adc8; margin-top: 2px; }

    /* divider */
    hr { border-color: #1e2d45; margin: 1rem 0; }

    /* missing context */
    .missing {
        background: #1a1a1a; border: 1px dashed #45475a;
        border-radius: 6px; padding: 0.6rem 1rem;
        font-size: 0.82rem; color: #6c7086; font-style: italic;
    }

    /* sidebar */
    section[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #1e2d45; }
    .stButton button {
        background: #1e2d45; color: #89b4fa; border: 1px solid #89b4fa;
        border-radius: 6px; font-family: 'IBM Plex Mono', monospace;
        font-size: 0.8rem; transition: all 0.15s;
    }
    .stButton button:hover { background: #89b4fa; color: #0a0e1a; }
</style>
""", unsafe_allow_html=True)


# ── render helper ─────────────────────────────────────────────────────────────

def source_pill(source: str) -> str:
    if not source:
        return ""
    return f"<span class='pill'>{source}</span>"

def render_result(result: dict):
    conf = result.get("confidence", "medium")
    conf_reason = result.get("confidence_reason", "")

    # ── header row ──
    col_sum, col_badge = st.columns([5, 1])
    with col_sum:
        st.markdown(f"<div class='summary-box'>{result.get('problem_summary', '—')}</div>", unsafe_allow_html=True)
    with col_badge:
        st.markdown(f"<br><span class='badge badge-{conf}'>{conf.upper()}</span>", unsafe_allow_html=True)
        if conf_reason:
            st.caption(conf_reason)

    # ── alerts ──
    if result.get("escalate"):
        st.markdown(
            f"<div class='card-alert'>🚨 <b>Escalation recommended</b> — {result.get('escalation_reason','')}</div>",
            unsafe_allow_html=True
        )

    pattern = result.get("pattern_alert", "")
    if pattern:
        st.markdown(
            f"<div class='card-pattern'>🔁 <b>Recurring pattern detected</b> — {pattern}</div>",
            unsafe_allow_html=True
        )

    missing = result.get("missing_context", "")
    if missing:
        st.markdown(f"<div class='missing'>ℹ️ {missing}</div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── causes + steps ──
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Likely Causes")
        causes = result.get("likely_causes", [])
        for i, item in enumerate(causes, 1):
            # handle both old format (string) and new format (dict)
            if isinstance(item, dict):
                text   = item.get("cause", "")
                source = item.get("source", "")
            else:
                text, source = item, ""
            st.markdown(
                f"<div class='item-row'>"
                f"<span class='item-num'>{i}.</span>"
                f"<span class='item-text'>{text}{source_pill(source)}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    with c2:
        st.markdown("### Recommended Steps")
        steps = result.get("recommended_next_steps", [])
        for i, item in enumerate(steps, 1):
            if isinstance(item, dict):
                text   = item.get("step", "")
                source = item.get("source", "")
            else:
                text, source = item, ""
            st.markdown(
                f"<div class='item-row'>"
                f"<span class='item-num'>{i}.</span>"
                f"<span class='item-text'>{text}{source_pill(source)}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── evidence ──
    c3, c4 = st.columns(2)

    with c3:
        st.markdown("### Manual Sections Cited")
        sections = result.get("supporting_manual_sections", [])
        if sections:
            for s in sections:
                st.markdown(f"<div class='card' style='padding:0.5rem 0.9rem; font-size:0.85rem;'>📄 {s}</div>", unsafe_allow_html=True)
        else:
            st.caption("None cited")

    with c4:
        st.markdown("### Similar Past Incidents")
        incidents = result.get("similar_past_incidents", [])
        if incidents:
            for inc in incidents:
                dt = f"{inc.get('downtime_hours', '?')}h downtime" if inc.get('downtime_hours') else ""
                st.markdown(
                    f"<div class='incident'>"
                    f"<span class='incident-id'>{inc.get('id','?')}</span>"
                    f"<span style='color:#6c7086; font-size:0.75rem; margin-left:8px;'>{inc.get('date','')}"
                    f"{'  ·  ' + dt if dt else ''}</span>"
                    f"<div class='incident-res'>→ {inc.get('resolution','')}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.caption("No similar incidents found")

    # ── raw chunks expander ──
    with st.expander("🔍 Raw retrieved chunks", expanded=False):
        st.markdown("**Manual hits**")
        for h in result.get("_retrieved_manual_hits", []):
            st.markdown(f"*Score {h['score']}* — `{h['metadata'].get('section','?')}`")
            st.code(h["text"][:400] + ("…" if len(h["text"]) > 400 else ""), language="markdown")
        st.markdown("**Log hits**")
        for h in result.get("_retrieved_log_hits", []):
            st.markdown(f"*Score {h['score']}* — Incident `{h['metadata'].get('incident_id','?')}`")
            st.code(h["text"][:400] + ("…" if len(h["text"]) > 400 else ""), language="markdown")


# ── session init ──────────────────────────────────────────────────────────────

if "chat_history"    not in st.session_state: st.session_state.chat_history    = []
if "session_history" not in st.session_state: st.session_state.session_history = []
if "ingested"        not in st.session_state: st.session_state.ingested        = False


# ── sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🔧 Tractian RAG")
    st.markdown("---")

    api_key = st.text_input(
        "Gemini API Key", type="password",
        value=os.environ.get("GEMINI_API_KEY", ""),
    )

    st.markdown("### Machine Context")
    machine_id = st.selectbox("Machine ID", ["MX-104"])
    company_id = st.selectbox("Company",    ["apex"])

    st.markdown("---")
    st.markdown("### Knowledge Base")

    if not st.session_state.ingested:
        if st.button("⚡ Ingest Sample Data", use_container_width=True):
            with st.spinner("Ingesting OEM manual..."):
                n_m = ingest_manual("data/manuals/cnc_mx104_manual.md", machine_id=machine_id, company_id=company_id)
            with st.spinner("Ingesting maintenance logs..."):
                n_l = ingest_log("data/logs/mx104_maintenance_log.md", company_id=company_id)
            st.session_state.ingested = True
            st.success(f"✅ {n_m} manual chunks + {n_l} incidents")
    else:
        st.success("✅ Knowledge base ready")
        if st.button("🔄 Re-ingest", use_container_width=True):
            st.session_state.ingested = False
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.chat_history    = []
        st.session_state.session_history = []
        st.rerun()

    st.markdown("""
    <small style='color:#45475a; font-family: IBM Plex Mono, monospace; font-size:0.7rem;'>
    Demo: MX-104 · Apex Mfg<br>
    Embeddings: all-MiniLM-L6-v2 (local)<br>
    LLM: Gemini 2.5 Flash Lite<br>
    VectorDB: Chroma (in-memory)<br><br>
    Prod: multi-tenant · Redis sessions<br>
    reranker · multimodal PDF parsing
    </small>""", unsafe_allow_html=True)


# ── main ──────────────────────────────────────────────────────────────────────

st.markdown("# 🔧 TRACTIAN / Maintenance Assistant")
st.caption(f"Machine: **{st.session_state.get('machine_id_display', 'MX-104')}** · Company: **Apex Manufacturing** · Dual-corpus RAG · Session memory enabled")

# render history
for turn in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant", avatar="🔧"):
        render_result(turn["result"])

# example buttons
st.markdown("**Quick examples:**")
EXAMPLES = [
    "Machine overheating after 2 hours",
    "Error code E-09 appeared",
    "When to replace the fan assembly?",
    "Spindle vibration alarm triggered",
]
cols = st.columns(len(EXAMPLES))
for i, eq in enumerate(EXAMPLES):
    if cols[i].button(eq, key=f"ex_{i}", use_container_width=True):
        st.session_state["prefill"] = eq
        st.rerun()

prefill    = st.session_state.pop("prefill", "")
user_input = st.chat_input("Describe the machine issue...") or prefill

if user_input:
    if not api_key:
        st.error("Add your Gemini API key in the sidebar.")
        st.stop()
    if not st.session_state.ingested:
        st.error("Click '⚡ Ingest Sample Data' first.")
        st.stop()

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant", avatar="🔧"):
        with st.spinner("Retrieving context + generating answer..."):
            result = query(
                question=user_input,
                api_key=api_key,
                machine_id=machine_id,
                company_id=company_id,
                session_history=st.session_state.session_history,
            )
        render_result(result)

    st.session_state.chat_history.append({"question": user_input, "result": result})
    st.session_state.session_history.append({
        "question": user_input,
        "summary":  result.get("problem_summary", ""),
    })
