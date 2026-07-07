import os
import time
import networkx as nx
from google import genai
from google.genai import types
from google.genai.errors import ServerError

# Initialize Gemini Client
client = genai.Client()

# In-memory cache of each project's extracted raw document text, keyed by
# project_id. Populated on first chat query and reused on every subsequent
# turn of the conversation -- avoids redundant disk I/O + PDF re-parsing on
# every single message. Invalidated via `invalidate_document_cache()`
# whenever a project's document set changes (upload/delete).
_RAW_TEXT_CACHE: dict[int, str] = {}


def invalidate_document_cache(project_id: int) -> None:
    """Drops the cached raw document text for a project, forcing the next
    chat query to re-read its documents from disk. Call this whenever a
    project's documents are uploaded, replaced, or deleted."""
    _RAW_TEXT_CACHE.pop(project_id, None)


def _execute_with_retry(contents, config_obj, max_retries: int = 4, backoff_delay: int = 5):
    """Retries transient Gemini server errors (503 UNAVAILABLE / 429 rate
    limit / resource exhaustion) with exponential backoff, mirroring the
    pattern already established in workflow/nodes/extraction_node.py."""
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model="gemini-2.5-flash", contents=contents, config=config_obj)
        except ServerError as se:
            error_msg = str(se)
            transient = "503" in error_msg or "429" in error_msg or "UNAVAILABLE" in error_msg or "Resource exhausted" in error_msg
            if transient and attempt < max_retries - 1:
                time.sleep(backoff_delay)
                backoff_delay *= 2
                continue
            raise

def load_project_graph(project_id: int) -> nx.DiGraph:
    """Loads the cached local NetworkX graph file for a specific project."""
    graph_path = f"backend/storage/project_{project_id}/graphs/knowledge_graph.gexf"
    
    if not os.path.exists(graph_path):
        print(f"⚠️ [Graph Engine] No compiled graph found for Project {project_id}. Creating an empty fallback graph.")
        return nx.DiGraph()
        
    try:
        return nx.read_gexf(graph_path)
    except Exception as e:
        print(f"❌ [Graph Engine] Error reading graph file: {e}")
        return nx.DiGraph()

def search_graph_context(G, query: str, max_depth: int = 2) -> str:
    """Traverses graph networks, extracting relevant nodes while discarding out-of-context branches."""
    relevant_subgraph_strings = []
    
    # Lowercase query terms for simple routing keyword matching
    query_lower = query.lower()
    is_construction_query = any(w in query_lower for w in ["delay", "billing", "milestone", "clause", "tender", "contractor", "penalty"])
    is_personal_query = any(w in query_lower for w in ["man", "lifestyle", "habit", "routine", "focus"])

    sample_edges = list(G.edges(data=True))[:125]
    for u, v, data in sample_edges:
        relation = data.get("label", "is connected to")
        
        # Simple string matching on node names to detect cross-domain entities safely
        node_text = f"{str(u)} {str(v)}".lower()
        
        # Smart Routing: Avoid cross-contamination matching
        if is_construction_query and any(p in node_text for p in ["becoming", "personal", "lifestyle", "hygiene", "habit"]):
            continue
        if is_personal_query and any(c in node_text for c in ["tender", "contract", "spec", "billing", "milestone"]):
            continue

        relevant_subgraph_strings.append(f"General Context: ({u})—[{relation}]—>({v})")
        
    if not relevant_subgraph_strings:
        return "No direct workspace structural relationships isolated for this specific query domain."
        
    return "\n".join(relevant_subgraph_strings)

def _load_raw_document_text(project_id: int) -> str:
    """
    Reads + concatenates the raw text of every document stored for a
    project, since the graph extraction may have only captured the
    index/headings. Result is cached per project_id (see _RAW_TEXT_CACHE)
    so repeated chat turns in the same conversation don't redundantly
    re-read + re-parse a large PDF from disk on every single message.
    """
    if project_id in _RAW_TEXT_CACHE:
        return _RAW_TEXT_CACHE[project_id]

    raw_text_context = ""
    docs_dir = f"backend/storage/project_{project_id}/documents"
    if os.path.exists(docs_dir):
        from pypdf import PdfReader
        for filename in os.listdir(docs_dir):
            filepath = os.path.join(docs_dir, filename)
            if os.path.isfile(filepath):
                raw_text_context += f"\n--- Document: {filename} ---\n"
                if filename.lower().endswith('.pdf'):
                    try:
                        reader = PdfReader(filepath)
                        for page in reader.pages:
                            text = page.extract_text()
                            if text:
                                raw_text_context += text + "\n"
                    except Exception as e:
                        print(f"Error reading PDF {filename}: {e}")
                else:
                    try:
                        with open(filepath, "r", errors="ignore") as f:
                            raw_text_context += f.read() + "\n"
                    except Exception as e:
                        print(f"Error reading file {filename}: {e}")

    # Truncate raw text if it's absurdly large, though Gemini 2.5 Flash handles 1M tokens.
    # 3 million characters is roughly 750k tokens, well within limits.
    if len(raw_text_context) > 3000000:
        raw_text_context = raw_text_context[:3000000] + "\n...[Content Truncated]..."

    _RAW_TEXT_CACHE[project_id] = raw_text_context
    return raw_text_context


def answer_project_query(project_id: int, user_question: str) -> str:
    """Combines graph network mapping with Gemini 2.5 Flash to answer cross-referencing user queries."""
    
    # Load the local knowledge graph file
    G = load_project_graph(project_id)
    
    # Extract structural relationship string context
    graph_context = search_graph_context(G, user_question)
    
    # Load the raw text of the documents (cached across chat turns) to
    # provide full context since the graph extraction may have only
    # captured the index/headings.
    raw_text_context = _load_raw_document_text(project_id)

    prompt = f"""
You are an expert EPC Construction Contract & Specification Auditor.
Your client is the main contractor seeking explicit evaluations on their uploaded commercial project documents.

CRITICAL GUARDRAIL:
You might find fragmented data fields or unrelated entity networks in the raw context map below (such as personal habits or lifestyle metrics). 
If the user's question is about construction engineering, schedules, or commercial billing, you MUST completely ignore all lifestyle or personal records. 
Never mix personal development metrics with corporate legal contracts.

Document Knowledge Graph Context (High-level relationships):
---
{graph_context}
---

Raw Document Text Context (Full details):
---
{raw_text_context}
---

User Question:
"{user_question}"

Provide a professional, definitive, and highly clear business summary response based on the provided Raw Document Text Context and Knowledge Graph. 
If the context does not explicitly contain the target facts, state cleanly that the active contract documents do not map those metrics, but do not hallucinate information.
"""

    try:
        # gemini-1.5-flash is retired on the v1beta endpoint this SDK talks
        # to (404 NOT_FOUND) -- gemini-2.5-flash is the current supported
        # flash variant, and is already the model used everywhere else in
        # this codebase (graph_rag.py, extraction_node.py, whatsapp_llm.py).
        # _execute_with_retry absorbs transient 503/429 "high demand" errors
        # with exponential backoff instead of surfacing them straight to
        # the chat UI on the first hiccup.
        response = _execute_with_retry(
            contents=prompt,
            config_obj=types.GenerateContentConfig(temperature=0.2),
        )
        return response.text
    except Exception as e:
        return f"❌ Failed to query graph execution architecture: {str(e)}"