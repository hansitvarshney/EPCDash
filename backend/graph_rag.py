import os
import json
import networkx as nx
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
from backend.database import ProjectDocument
from pypdf import PdfReader  # 📄 Added for PDF handling

# Initialize the Gemini Client
client = genai.Client()

def extract_entities_and_relations(text_content: str) -> dict:
    """Uses Gemini 2.5 Flash free tier to extract structured construction entities."""
    prompt = f"""
    Analyze the following construction project contract/specification text snippet.
    Extract key Entities (e.g., Corporate roles, technical equipment, penalty terms, legal clauses)
    and their operational Relationships.
    
    Return the response strictly as a valid JSON object matching this schema:
    {{
        "entities": [
            {{"id": "EntityName", "type": "TYPE_TAG"}}
        ],
        "relationships": [
            {{"source": "EntityNameA", "target": "EntityNameB", "relation": "how they connect"}}
        ]
    }}
    
    Text snippet to process:
    ---
    {text_content}
    ---
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ [Graph Extraction Snippet Error]: {e}")
        return {"entities": [], "relationships": []}

def build_project_knowledge_graph(project_id: int, db: Session):
    """Crawls all indexed local text/PDF files for a project and compiles a knowledge graph."""
    G = nx.DiGraph()
    documents = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).all()
    
    print(f"🕸️ [GraphRAG] Compiling Graph for Project {project_id} across {len(documents)} files.")
    
    for doc in documents:
        if not os.path.exists(doc.storage_path):
            continue
            
        content = ""
        # 📄 Check if file is a PDF, otherwise fallback to plain text parsing
        if doc.storage_path.lower().endswith('.pdf'):
            try:
                reader = PdfReader(doc.storage_path)
                # Pull first few pages to stay safely within free rate limits for our test runs
                for page in reader.pages[:5]: 
                    text = page.extract_text()
                    if text:
                        content += text + "\n"
            except Exception as pdf_err:
                print(f"❌ Failed to parse PDF {doc.file_name}: {pdf_err}")
                continue
        else:
            with open(doc.storage_path, "r", errors="ignore") as f:
                content = f.read()
                
        if not content.strip():
            continue

        snippet = content[:6000] 
        graph_data = extract_entities_and_relations(snippet)
        
        for entity in graph_data.get("entities", []):
            G.add_node(entity["id"], type=entity["type"])
            
        for rel in graph_data.get("relationships", []):
            G.add_edge(rel["source"], rel["target"], label=rel["relation"])
            
    graph_dir = f"backend/storage/project_{project_id}/graphs"
    os.makedirs(graph_dir, exist_ok=True)
    graph_path = os.path.join(graph_dir, "knowledge_graph.gexf")
    
    nx.write_gexf(G, graph_path)
    print(f"✅ [GraphRAG] Master Knowledge Graph written to disk at: {graph_path}")
    return G