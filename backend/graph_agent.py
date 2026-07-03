import io
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from PIL import Image
from langgraph.graph import StateGraph, END
from google import genai
from google.genai import types

# Reuse your existing schema layout definitions
from backend.schemas import AdaptiveLifecycleSchema, ADAPTIVE_LIFECYCLE_CONTEXT

# 1. Define our State structure 
class AgentState(BaseModel):
    image_bytes: bytes
    project_id: int
    parsed_payload: Optional[Dict[str, Any]] = None
    audit_errors: List[str] = []
    is_ready_for_db: bool = False

# 2. Node A: The Intelligent Vision Parser Node
def extraction_node(state: AgentState) -> Dict[str, Any]:
    client = genai.Client()
    image = Image.open(io.BytesIO(state.image_bytes))
    
    # Combined base framework context with hard handwriting verification instructions
    ocr_prompt = f"""
    {ADAPTIVE_LIFECYCLE_CONTEXT}
    
    CRITICAL EXTRACTOR RULES FOR HANDWRITING DIGIT AMBIGUITY:
    1. Look incredibly closely at fields like 'Masons' and 'Helpers'. Site supervisors frequently write '15' with a swift cursive flourish, heavy slant, or pen bleed that easily misreads as an '18'.
    2. Cross-check your row-by-row arithmetic values against explicit totals written anywhere else on the sheet (e.g., "Total workers: 40 Nos" or aggregate section logs).
    3. If the itemized sum of Masons + Helpers does not equal the documented total workforce count, re-evaluate the pixel data of ambiguous digits to enforce strict mathematical consistency with the supervisor's stated total sum.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[image, ocr_prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AdaptiveLifecycleSchema,
            temperature=0.1,  # Lower temperature keeps the model structurally objective
        ),
    )
    
    # Parse into raw dictionary format for the State container
    parsed_json = json.loads(response.text)
    return {"parsed_payload": parsed_json}

# 3. Node B: The Compliance & Mathematical Audit Node
def compliance_audit_node(state: AgentState) -> Dict[str, Any]:
    payload = state.parsed_payload
    errors = []
    
    if not payload or "quantity_entries" not in payload:
        return {"audit_errors": ["Empty or failed payload generation."], "is_ready_for_db": False}
        
    # Programmatic mathematical verification block
    for idx, entry in enumerate(payload.get("quantity_entries", [])):
        # If the LLM flagged it or if we calculate a custom discrepancy
        if not entry.get("is_mathematically_correct", True):
            errors.append(f"Row {idx+1} (ID: {entry.get('structural_id')}): Math discrepancy flagged in field notes.")
            
    return {
        "audit_errors": errors,
        "is_ready_for_db": True  # Ready to advance to ledger commit pipeline
    }

# 4. Initialize and Compile our Orchestration Architecture
workflow = StateGraph(AgentState)

# Mount our custom operational blocks
workflow.add_node("parser_extractor", extraction_node)
workflow.add_node("compliance_auditor", compliance_audit_node)

# Map our data path mapping line
workflow.set_entry_point("parser_extractor")
workflow.add_edge("parser_extractor", "compliance_auditor")
workflow.add_edge("compliance_auditor", END)

# Compile into an executable application agent
audit_graph_agent = workflow.compile()