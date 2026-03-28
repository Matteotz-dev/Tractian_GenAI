"""
rag_engine.py — Tractian RAG core
Handles ingestion and retrieval for manuals and logs.
Uses local sentence-transformers embeddings (no API needed for retrieval).
LLM call (Anthropic) only happens at query time.
"""

import os
import re
import json
import chromadb
from chromadb.utils import embedding_functions

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

EMBED_MODEL = "all-MiniLM-L6-v2"  # local, fast, free
MANUAL_COLLECTION = "manuals"
LOGS_COLLECTION   = "logs"

# ──────────────────────────────────────────────
# CHROMA SETUP
# ──────────────────────────────────────────────

_client = chromadb.Client()  # in-memory for demo

_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBED_MODEL
)

_manual_col = _client.get_or_create_collection(
    name=MANUAL_COLLECTION,
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"}
)

_logs_col = _client.get_or_create_collection(
    name=LOGS_COLLECTION,
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"}
)

# ──────────────────────────────────────────────
# CHUNKING
# ──────────────────────────────────────────────

def chunk_manual(text: str, max_tokens: int = 400) -> list[dict]:
    """
    Section-aware chunking for OEM manuals.
    Splits at '## ' headers; each chunk carries its section title as metadata.
    Large sections are further split by paragraph.
    """
    sections = re.split(r'\n(?=## )', text)
    chunks = []
    for section in sections:
        lines = section.strip().split('\n')
        title = lines[0].lstrip('#').strip() if lines else "Unknown"
        body  = '\n'.join(lines[1:]).strip()

        # rough token estimate: 1 token ≈ 4 chars
        if len(body) // 4 <= max_tokens:
            if body:
                chunks.append({"text": f"[{title}]\n{body}", "section": title})
        else:
            # split large sections by paragraph
            paras = re.split(r'\n\n+', body)
            for para in paras:
                if para.strip():
                    chunks.append({"text": f"[{title}]\n{para.strip()}", "section": title})
    return chunks


def chunk_logs(text: str) -> list[dict]:
    """
    Incident-aware chunking for maintenance logs.
    Each '## Incident' block becomes one chunk with structured metadata extracted.
    """
    incidents = re.split(r'\n(?=## Incident)', text)
    chunks = []
    for block in incidents:
        block = block.strip()
        if not block or not block.startswith('## Incident'):
            continue

        # extract metadata fields from markdown bold labels
        def extract(label):
            m = re.search(rf'\*\*{label}:\*\*\s*(.+)', block)
            return m.group(1).strip() if m else ""

        chunks.append({
            "text": block,
            "incident_id": extract("Incident").replace('#', '').strip() or "unknown",
            "date":        extract("Date"),
            "technician":  extract("Technician"),
            "machine_id":  extract("Machine"),
        })
    return chunks

# ──────────────────────────────────────────────
# INGESTION
# ──────────────────────────────────────────────

def ingest_manual(path: str, machine_id: str = "MX-104", company_id: str = "apex"):
    text = open(path).read()
    chunks = chunk_manual(text)
    if not chunks:
        return 0

    _manual_col.add(
        documents=[c["text"] for c in chunks],
        metadatas=[{
            "source":     os.path.basename(path),
            "section":    c["section"],
            "machine_id": machine_id,
            "company_id": company_id,
            "type":       "manual",
        } for c in chunks],
        ids=[f"manual_{machine_id}_{i}" for i, _ in enumerate(chunks)]
    )
    return len(chunks)


def ingest_log(path: str, company_id: str = "apex"):
    text = open(path).read()
    chunks = chunk_logs(text)
    if not chunks:
        return 0

    _logs_col.add(
        documents=[c["text"] for c in chunks],
        metadatas=[{
            "source":      os.path.basename(path),
            "incident_id": c["incident_id"],
            "date":        c["date"],
            "technician":  c["technician"],
            "machine_id":  c["machine_id"],
            "company_id":  company_id,
            "type":        "log",
        } for c in chunks],
        ids=[f"log_{c['incident_id'].replace(' ', '_')}_{i}" for i, c in enumerate(chunks)]
    )
    return len(chunks)

# ──────────────────────────────────────────────
# RETRIEVAL
# ──────────────────────────────────────────────

def retrieve(
    query:      str,
    machine_id: str = "MX-104",
    company_id: str = "apex",
    top_k:      int = 3
) -> dict:
    """
    Dual-collection retrieval with metadata filtering.
    Returns separate manual and log results.
    """
    where = {"$and": [{"machine_id": machine_id}, {"company_id": company_id}]}

    manual_results = _manual_col.query(
        query_texts=[query],
        n_results=min(top_k, _manual_col.count()),
        where=where,
    )

    log_results = _logs_col.query(
        query_texts=[query],
        n_results=min(top_k, _logs_col.count()),
        where=where,
    )

    def unpack(results):
        docs  = results["documents"][0]  if results["documents"]  else []
        metas = results["metadatas"][0]  if results["metadatas"]  else []
        dists = results["distances"][0]  if results["distances"]  else []
        return [
            {"text": d, "metadata": m, "score": round(1 - dist, 3)}
            for d, m, dist in zip(docs, metas, dists)
        ]

    return {
        "manual_hits": unpack(manual_results),
        "log_hits":    unpack(log_results),
    }

# ──────────────────────────────────────────────
# PROMPT BUILDER
# ──────────────────────────────────────────────

def build_prompt(
    question:     str,
    manual_hits:  list,
    log_hits:     list,
    session_history: list[dict] | None = None
) -> str:
    manual_ctx = "\n\n".join(
        f"[Manual — {h['metadata'].get('section','?')}]\n{h['text']}"
        for h in manual_hits
    ) or "No manual sections retrieved."

    log_ctx = "\n\n".join(
        f"[Past Incident {h['metadata'].get('incident_id','?')} — {h['metadata'].get('date','?')}]\n{h['text']}"
        for h in log_hits
    ) or "No past incidents retrieved."

    history_str = ""
    if session_history:
        history_str = "\n\nCONVERSATION HISTORY (most recent last):\n"
        for turn in session_history[-4:]:  # keep last 4 turns to stay within context
            history_str += f"Technician: {turn['question']}\nAssistant: {turn['summary']}\n"

    return f"""You are an expert maintenance assistant for industrial CNC machines, embedded inside Tractian's platform.
Your job is to help on-site technicians diagnose issues quickly and accurately.

STRICT RULES:
- Use ONLY the context provided below. Do not invent facts.
- Every cause and every next step MUST cite the specific manual section or incident ID that supports it.
- If the context does not contain enough information to answer confidently, say so explicitly in "missing_context".
- Be concise and actionable — technicians are on the shop floor, not reading a report.
- If the same issue has recurred multiple times in the logs, flag that pattern explicitly.
{history_str}
════════════════════════════════════════
MANUAL SECTIONS RETRIEVED:
{manual_ctx}

PAST INCIDENTS RETRIEVED:
{log_ctx}
════════════════════════════════════════

TECHNICIAN QUESTION: {question}

Respond in this EXACT JSON format. Raw JSON only — no markdown fences, no extra text:
{{
  "problem_summary": "1-2 sentence summary of the most likely issue based on the context",
  "likely_causes": [
    {{"cause": "description of cause", "source": "Manual: Section Name OR Incident: LOG-XXXX"}}
  ],
  "recommended_next_steps": [
    {{"step": "concrete action to take", "source": "Manual: Section Name OR Incident: LOG-XXXX"}}
  ],
  "pattern_alert": "if this issue has recurred 2+ times in logs, describe the pattern here, else empty string",
  "supporting_manual_sections": ["exact section name from context"],
  "similar_past_incidents": [
    {{"id": "LOG-XXXX", "date": "YYYY-MM-DD", "resolution": "what fixed it", "downtime_hours": 0}}
  ],
  "missing_context": "what information would help give a better answer, or empty string if context was sufficient",
  "confidence": "high | medium | low",
  "confidence_reason": "one sentence explaining why",
  "escalate": true,
  "escalation_reason": "only if escalate is true, else empty string"
}}"""

# ──────────────────────────────────────────────
# LLM CALL (Gemini)
# ──────────────────────────────────────────────

def call_claude(prompt: str, api_key: str) -> dict:
    from google import genai
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
    )
    raw = response.text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw)


# ──────────────────────────────────────────────
# FULL PIPELINE
# ──────────────────────────────────────────────

def query(
    question:        str,
    api_key:         str,
    machine_id:      str = "MX-104",
    company_id:      str = "apex",
    session_history: list[dict] | None = None
) -> dict:
    hits   = retrieve(question, machine_id, company_id)
    prompt = build_prompt(
        question,
        hits["manual_hits"],
        hits["log_hits"],
        session_history
    )
    result = call_claude(prompt, api_key)
    result["_retrieved_manual_hits"] = hits["manual_hits"]
    result["_retrieved_log_hits"]    = hits["log_hits"]
    return result
