# Tractian RAG — Maintenance Assistant Prototype

> Matteo Ugliotti · Georgia Tech

---

## ⚠️ Development Notes

This project was built with AI assistance, I want to be upfront about that:

- **Architecture and design** iterated with Claude (claude.ai) and ChatGPT (chatgpt.com) to pressure-test design decisions: chunking strategy, dual-corpus isolation rationale, framework choice (why custom loop over LangGraph), session memory token budget, and structured output schema
- **Code** initial scaffold generated with Claude, then debugged, extended, and adapted manually to make it actually run
- **The ideas, tradeoffs, and justifications are my own** I can explain and defend design decision in this repo

This is how I'd work at a company that builds AI products: use the tools, own the thinking.

---

## What This Is

A minimal working RAG system that helps on-site technicians diagnose machine issues by instantly surfacing:

- Relevant sections from OEM manuals (static PDF corpus)
- Similar past incidents from historical maintenance logs (dynamic Markdown corpus)

Built as a prototype to demonstrate the core design decisions in the case submission — not a production system.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    INGESTION                        │
│                                                     │
│  OEM Manuals (PDF/MD)     Historical Logs (MD)      │
│  section-aware chunking   incident-level chunks     │
│  300–600 tok + parent     one chunk per incident    │
│  captions for images      metadata: machine, date   │
│         │                          │                │
│         ▼                          ▼                │
│   manuals_store              logs_store             │
│   (Chroma collection)        (Chroma collection)    │
└──────────────────┬──────────────────┬──────────────┘
                   │                  │
┌──────────────────▼──────────────────▼──────────────┐
│                   RETRIEVAL                         │
│                                                     │
│  Query → filter by company_id + machine_id          │
│       → retrieve top-k from each collection        │
│       → merge results                               │
│       → (prod: cross-encoder rerank)                │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│                  GENERATION                         │
│                                                     │
│  Session history (last 4 turns)                     │
│  + Manual chunks                                    │
│  + Log chunks                                       │
│  + Technician question                              │
│       → LLM (Gemini 2.5 Flash)                      │
│       → Structured JSON output                      │
└─────────────────────────────────────────────────────┘
```

### Structured Output Schema

Every response returns:

```json
{
  "problem_summary": "...",
  "likely_causes": [{"cause": "...", "source": "Manual: Section X"}],
  "recommended_next_steps": [{"step": "...", "source": "Incident: LOG-XXXX"}],
  "similar_past_incidents": [{"id": "...", "date": "...", "resolution": "...", "downtime_hours": 0}],
  "pattern_alert": "...",
  "missing_context": "...",
  "confidence": "high | medium | low",
  "confidence_reason": "...",
  "escalate": false,
  "escalation_reason": ""
}
```

Every `cause` and `step` cites the exact source chunk — this forces the LLM to ground answers in retrieved evidence and gives the technician something to verify.

`missing_context` is the most important field for safety: when retrieved evidence is insufficient, the system says so explicitly rather than hallucinating confidence.

---

## What the Prototype Actually Demonstrates

| Feature | Status | Notes |
|---|---|---|
| Dual-corpus ingestion | ✅ Built | Separate Chroma collections for manuals and logs |
| Metadata filtering | ✅ Built | Filters by `company_id` + `machine_id` before search |
| Session memory | ✅ Built | Last 4 turns passed as `{question, summary}` pairs |
| Source citations | ✅ Built | Every cause and step cites its chunk |
| Pattern detection | ✅ Built | `pattern_alert` flags recurring issues |
| Escalation flags | ✅ Built | `escalate` + `confidence` fields in output |
| `missing_context` honesty | ✅ Built | Explicit when evidence is insufficient |
| Cross-encoder reranker | 🔲 Designed | Production: Cohere Rerank or BGE cross-encoder |
| Redis session persistence | 🔲 Designed | Demo uses in-memory; prod keys by `session_id` with TTL |
| Multi-tenant isolation | 🔲 Designed | Demo hardcoded to one company/machine |
| OCR / multimodal for images | 🔲 Designed | Production: unstructured.io + vision-LM |
| Parent-child chunk linking | 🔲 Designed | Demo uses flat chunks |
| Event-driven log ingestion | 🔲 Designed | Demo ingests on startup |

This distinction matters. The demo is a proof of concept, not a production deployment. Every "Designed" item has an explicit production path described in the case submission slides.

---

## Project Structure

```
tractian-rag/
├── README.md
├── requirements.txt
├── app.py                              # Streamlit UI
├── rag_engine.py                       # Core RAG logic: ingestion, retrieval, LLM call
└── data/
    ├── manuals/
    │   └── cnc_mx104_manual.md         # Synthetic OEM manual (CNC milling machine)
    └── logs/
        └── mx104_maintenance_log.md    # Synthetic maintenance log (5 incidents)
```

### Key files

**`rag_engine.py`** — everything that matters:
- `chunk_manual()` — section-aware chunking with header extraction
- `chunk_logs()` — incident-aware chunking with structured metadata extraction
- `ingest_manual()` / `ingest_log()` — load into separate Chroma collections with metadata
- `retrieve()` — metadata-filtered dual-corpus retrieval
- `build_prompt()` — assembles system prompt + session history + retrieved context
- `call_claude()` — LLM call returning structured JSON (currently Gemini; production: Claude Sonnet or GPT-4o)
- `query()` — full pipeline: retrieve → prompt → parse → return

**`app.py`** — Streamlit UI:
- Sidebar: API key input, machine/company selector, ingest button, session controls
- Main: chat interface with structured answer rendering (causes, steps, incidents, confidence)
- Expander: raw retrieved chunks with similarity scores — shows the dual-corpus retrieval working

---

## Setup

```bash
# 1. Create virtual environment
python3 -m venv tractian-env
source tractian-env/bin/activate   # Windows: tractian-env\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Get a free Gemini API key
# → aistudio.google.com → API Keys → Create
# Note: Gemini 2.5 Flash free tier is sufficient for this demo
# Production would use Claude Sonnet or GPT-4o for stronger reasoning and tool use

# 4. Run
streamlit run app.py
```

Then:
1. Paste your Gemini API key in the sidebar
2. Click **⚡ Ingest Sample Data**
3. Try one of the example questions or type your own

---

## Sample Data

Two synthetic files designed to test the system realistically:

**`cnc_mx104_manual.md`** — OEM manual for a CNC milling machine covering:
- Cooling system specs (fan RPM thresholds, coolant flow rates, error codes E-01 through E-17)
- Spindle maintenance intervals and runout tolerances
- Scheduled maintenance table (250h to 8000h intervals)

**`mx104_maintenance_log.md`** — 5 historical incidents covering:
- Fan assembly failure (LOG-0041, LOG-0078)
- Coolant loop blockage (LOG-0055)
- Pump lubrication overdue (LOG-0063)
- Spindle bearing wear (LOG-0071)

The two fan incidents (LOG-0041 and LOG-0078) are intentionally similar — they trigger the `pattern_alert` field when asking about overheating, demonstrating recurrence detection across sessions.

---

## Example Queries

Calibrated to the sample data, each demonstrating a different system behavior:

| Query | What it shows |
|---|---|
| `"Machine overheating after 2 hours"` | Full pipeline: manual + log retrieval, pattern alert on 2 fan incidents |
| `"Error code E-09 appeared"` | Manual-heavy retrieval, specific error code lookup |
| `"When does the fan assembly need replacing?"` | Pure manual retrieval, scheduled maintenance |
| `"Spindle vibration alarm triggered"` | Log-heavy retrieval, bearing incident |
| `"Follow-up: what if it happens again?"` | Session memory in action — references prior turn |

---

## What I'd Improve Next

In order of priority:

1. **Cross-encoder reranker** — the biggest gap between demo and production. MiniLM cosine similarity works but misses the OEM ↔ technician language gap. Cohere Rerank or BGE would meaningfully improve retrieval precision.

2. **Parent-child chunking** — currently flat section chunks. True parent-child linking (retrieve child for precision, expand to parent for LLM context) would improve answer quality on dense manual sections.

3. **Redis session persistence** — in-memory session dies on restart. Production needs server-side persistence keyed by `session_id` with shift-length TTL.

4. **Evaluation harness** — no offline eval yet. Would add: recall@k on a labeled query set, citation accuracy, latency benchmarking, `missing_context` rate as a calibration signal.

5. **Multi-tenant hardening** — demo is hardcoded to one company/machine. Production needs namespace isolation at the Chroma collection level, not just metadata filtering.

---

## Requirements

```
google-genai>=0.28.1
chromadb>=0.5.0
streamlit>=1.35.0
sentence-transformers>=3.0.0
```
