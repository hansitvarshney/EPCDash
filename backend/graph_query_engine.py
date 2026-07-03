import os
import networkx as nx
from google import genai
from google.genai import types

# Initialize Gemini Client
client = genai.Client()

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

def answer_project_query(project_id: int, user_question: str) -> str:
    """Combines graph network mapping with Gemini 1.5 Flash to answer cross-referencing user queries."""
    
    # Load the local knowledge graph file
    G = load_project_graph(project_id)
    
    # Extract structural relationship string context
    graph_context = search_graph_context(G, user_question)
    
    prompt = f"""
You are an expert EPC Construction Contract & Specification Auditor.
Your client is the main contractor seeking explicit evaluations on their uploaded commercial project documents.

CRITICAL GUARDRAIL:
You might find fragmented data fields or unrelated entity networks in the raw context map below (such as personal habits or lifestyle metrics). 
If the user's question is about construction engineering, schedules, or commercial billing, you MUST completely ignore all lifestyle or personal records. 
Never mix personal development metrics with corporate legal contracts.

Document Knowledge Graph Context:
---
{graph_context}
---

User Question:
"{user_question}"

Provide a professional, definitive, and highly clear business summary response. 
If the context does not explicitly contain the target facts, state cleanly that the active contract index does not map those metrics, but do not hallucinate information from unrelated nodes.
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2
            )
        )
        return response.text
    except Exception as e:
        return f"❌ Failed to query graph execution architecture: {str(e)}"