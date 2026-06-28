import os
import io
import openpyxl
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
from PIL import Image
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from dotenv import load_dotenv

# 1. Load local environment keys from .env FIRST before initializing clients
load_dotenv()

# Absolute Package Imports to support executing from the workspace root
from backend.database import SessionLocal, Project, DailySiteLog, LaborLedger, DailyWorkMetrics
from backend.analytics import AnalyticsEngine

app = FastAPI(title="EPC Adaptive Lifecycle Parser Platform Engine")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 2. Initialize Google GenAI client (safely picks up GEMINI_API_KEY now)
client = genai.Client()

# ═════════════════════════════════════════════════════════
# 📋 SYSTEM SCHEMAS & LAYOUT CONFIGURATIONS
# ═════════════════════════════════════════════════════════

class AdaptiveLayoutConfig:
    DEFAULT_TEMPLATE_PATH = "templates/master_site_template.xlsx"
    METADATA_DATE_CELL = "B3"
    METADATA_CATEGORY_CELL = "B4"
    HAS_LABOR_SECTION = True
    LABOR_ROW_START = 6
    QUANTITY_ROW_START = 18

class ResourceAllocationEntry(BaseModel):
    header_a: str = Field(description="Contractor / Vendor Subcontractor corporate agency name entity.")
    header_b: str = Field(description="Detailed trade role or deployment crew description classification.")
    metric_1: int = Field(description="Count or volume score metric representing active skilled workforce (Masons).")
    metric_2: int = Field(description="Count volume metric of active helper forces (Laborers / Helpers).")
    description_notes: str = Field(description="Assigned site location, structural target milestone or operational notes.")

class StructuralQuantityEntry(BaseModel):
    structural_id: str = Field(description="Structural tag designator element context ID label matching design plan.")
    sub_tag: Optional[str] = Field(None, description="Diameter thickness breakdown specifier notation or secondary bar tag layer.")
    raw_formula_notation: str = Field(description="The formula expression equation string parsed exactly from handwriting.")
    claimed_value: float = Field(description="Calculated measurement area volume weight value requested by supervisor.")
    unit: str = Field(description="Standard metric unit of construction dimensioning.")
    is_mathematically_correct: bool = Field(description="Boolean checking if length*width*multiplier arithmetically matches claimed_value.")
    audit_notes: str = Field(description="Clear explanation highlighting specific math errors or validation discrepancy details.")

class AdaptiveLifecycleSchema(BaseModel):
    report_date: str = Field(description="Calendar target execution milestone date parsed uniformly as YYYY-MM-DD format.")
    log_category: str = Field(description="Operational process tracking scope index token standard (e.g., REINFORCEMENT_BBS, SHUTTERING, CONCRETING).")
    declared_total_quantity: float = Field(description="Aggregated master structural summary progress output declared on document.")
    resource_entries: List[ResourceAllocationEntry] = Field(default=[], description="Extracted records tracking manpower assets present.")
    quantity_entries: List[StructuralQuantityEntry] = Field(description="Granular calculation rows auditing lines of structural items.")

ADAPTIVE_LIFECYCLE_CONTEXT = """
You are an expert EPC Construction Audit System specializing in Indian infrastructural projects. 
Analyze the provided handwritten site report image and extract data matching the required schema structure.

CRITICAL ASSIGNMENTS:
1. Parse handwritten formulas accurately. Recalculate the dimensions yourself to audit the claimed math.
2. If the arithmetic product of the parameters does not match the 'claimed_value', flag 'is_mathematically_correct' as false and specify the discrepancy in 'audit_notes'.
"""

# ═════════════════════════════════════════════════════════
# 🚀 CORE ROUTE ENGINE
# ═════════════════════════════════════════════════════════

@app.post("/api/v1/fanout-ingest")
async def fanout_ingest(
    project_id: int, 
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        project = Project(id=project_id, name=f"Gurgaon Sector Layout Project {project_id}")
        db.add(project)
        db.commit()

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # 1. Execute Intelligent GenAI Data Extraction
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image, ADAPTIVE_LIFECYCLE_CONTEXT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AdaptiveLifecycleSchema,
                temperature=0.0,
            ),
        )

        parsed_data = AdaptiveLifecycleSchema.model_validate_json(response.text)
        
        # 2. Persist Structural Log Metadata Anchor
        site_log = DailySiteLog(
            project_id=project_id,
            report_date=parsed_data.report_date,
            category=parsed_data.log_category
        )
        db.add(site_log)
        db.flush() 

        # 3. Mount Excel Base Layout Asset
        template_path = AdaptiveLayoutConfig.DEFAULT_TEMPLATE_PATH
        if not os.path.exists(template_path):
            raise HTTPException(status_code=500, detail=f"Master Excel template missing at path: {template_path}.")
            
        wb = openpyxl.load_workbook(template_path)
        
        amber_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        alert_font = Font(name="Calibri", size=11, bold=True, color="B78103")
        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9')
        )

        ws_log = wb["Daily_Progress_Log"]
        ws_log[AdaptiveLayoutConfig.METADATA_DATE_CELL] = parsed_data.report_date
        ws_log[AdaptiveLayoutConfig.METADATA_CATEGORY_CELL] = parsed_data.log_category

        # --- TAB 1 & DB: RESOURCE ALLOCATION FORCE ROSTER ---
        if AdaptiveLayoutConfig.HAS_LABOR_SECTION and parsed_data.resource_entries:
            l_row = AdaptiveLayoutConfig.LABOR_ROW_START
            for r_entry in parsed_data.resource_entries:
                ws_log[f"A{l_row}"] = r_entry.header_a
                ws_log[f"B{l_row}"] = r_entry.header_b
                ws_log[f"C{l_row}"] = r_entry.metric_1
                ws_log[f"D{l_row}"] = r_entry.metric_2
                ws_log[f"E{l_row}"] = r_entry.description_notes
                
                db_labor = LaborLedger(
                    log_id=site_log.id,
                    contractor_name=r_entry.header_a,
                    crew_type=r_entry.header_b,
                    masons_count=r_entry.metric_1,
                    helpers_count=r_entry.metric_2,
                    assigned_activity=r_entry.description_notes
                )
                db.add(db_labor)
                l_row += 1

        # --- TAB 1 & DB: PROGRESS ENTRIES ---
        q_row = AdaptiveLayoutConfig.QUANTITY_ROW_START
        for q_entry in parsed_data.quantity_entries:
            ws_log[f"A{q_row}"] = q_entry.structural_id
            ws_log[f"B{q_row}"] = q_entry.sub_tag if q_entry.sub_tag else ""
            ws_log[f"C{q_row}"] = q_entry.raw_formula_notation
            ws_log[f"D{q_row}"] = q_entry.claimed_value
            ws_log[f"E{q_row}"] = q_entry.unit
            
            db_metric = DailyWorkMetrics(
                log_id=site_log.id,
                category=parsed_data.log_category,
                element_id=q_entry.structural_id,
                sub_component=q_entry.sub_tag,
                formula_notation=q_entry.raw_formula_notation,
                metric_value=q_entry.claimed_value,
                unit=q_entry.unit
            )
            db.add(db_metric)

            if not q_entry.is_mathematically_correct:
                ws_log[f"D{q_row}"].fill = amber_fill
                ws_log[f"F{q_row}"] = q_entry.audit_notes
                ws_log[f"F{q_row}"].fill = amber_fill
                ws_log[f"F{q_row}"].font = alert_font
                ws_log[f"F{q_row}"].alignment = Alignment(wrap_text=True)
                ws_log[f"F{q_row}"].border = thin_border
            q_row += 1

        # 4. --- TAB 2: MATERIAL INVENTORY ---
        ws_inv = wb["Inventory_Reconciliation"]
        if parsed_data.log_category == "REINFORCEMENT_BBS":
            total_steel_used = sum([item.claimed_value for item in parsed_data.quantity_entries])
            current_inv_value = ws_inv["D5"].value if ws_inv["D5"].value else 0
            ws_inv["D5"] = current_inv_value + total_steel_used

        # 5. --- TAB 3: SCHEDULE LIFECYCLE TIMELINE ---
        ws_sch = wb["Project_Baseline_Tracker"]
        if parsed_data.log_category == "SHUTTERING":
            current_cumulative = ws_sch["D5"].value if ws_sch["D5"].value else 0
            ws_sch["D5"] = current_cumulative + parsed_data.declared_total_quantity

        db.flush()

        # ═════════════════════════════════════════════════════════
        # 📊 STEP 5b: COMPILE MACRO EXECUTIVE ANALYTICS TAB
        # ═════════════════════════════════════════════════════════
        project_metrics = AnalyticsEngine.get_project_summary(db, project_id)
        
        if "Executive_Analytics" in wb.sheetnames:
            wb.remove(wb["Executive_Analytics"])
            
        ws_analytics = wb.create_sheet(title="Executive_Analytics")
        ws_analytics.views.sheetView[0].showGridLines = True
        
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        accent_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        white_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        bold_font = Font(name="Calibri", size=11, bold=True)
        regular_font = Font(name="Calibri", size=11)
        
        ws_analytics["A1"] = "PROJECT EXECUTIVE RUN-RUN CONTROL CENTER"
        ws_analytics["A1"].font = Font(name="Calibri", size=16, bold=True, color="1F4E78")
        
        ws_analytics["A3"] = "Historical Resource Allocation Deployed"
        ws_analytics["A3"].font = bold_font
        
        ws_analytics.append(["Metric Type", "Total Accumulated Man-Days Deployed"])
        ws_analytics.append(["Skilled Force (Masons)", project_metrics["manpower_deployed"]["cumulative_masons"]])
        ws_analytics.append(["Helper Support Forces", project_metrics["manpower_deployed"]["cumulative_helpers"]])
        ws_analytics.append(["Total Project Labor Force Burn", project_metrics["manpower_deployed"]["total_man_days"]])
        
        for col in range(1, 3):
            ws_analytics.cell(row=7, column=col).fill = accent_fill
            ws_analytics.cell(row=7, column=col).font = bold_font
            
        ws_analytics["A9"] = "Cumulative Executed Quantities"
        ws_analytics["A9"].font = bold_font
        
        headers_qty = ["Work Category", "Structural Element Reference", "Total Output Executed To Date", "Unit of Measure"]
        ws_analytics.append(headers_qty)
        
        for col_idx, text in enumerate(headers_qty, start=1):
            cell = ws_analytics.cell(row=10, column=col_idx)
            cell.fill = header_fill
            cell.font = white_font
            cell.alignment = Alignment(horizontal="center")

        for entry in project_metrics["quantities_executed"]:
            ws_analytics.append([
                entry["category"],
                entry["element_id"],
                entry["total_output"],
                entry["unit"]
            ])
            
        for row in ws_analytics.iter_rows(min_row=4, max_row=ws_analytics.max_row, min_col=1, max_col=4):
            for cell in row:
                if cell.row not in [4, 10]:
                    cell.font = regular_font
                    if isinstance(cell.value, (int, float)):
                        cell.number_format = '#,##0.00'

        for col in ws_analytics.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws_analytics.column_dimensions[col_letter].width = max(max_len + 3, 14)

        db.commit()
        sanitized_date = parsed_data.report_date.replace("-", "")
        output_filename = f"outputs/Master_Dashboard_Update_{project_id}_{sanitized_date}.xlsx"
        wb.save(output_filename)

        return FileResponse(
            path=output_filename,
            filename=f"Master_Dashboard_Update_{parsed_data.report_date}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ═════════════════════════════════════════════════════════
# 📊 STANDALONE ANALYTICS ENDPOINTS
# ═════════════════════════════════════════════════════════

@app.get("/api/v1/analytics/summary/{project_id}")
def get_project_analytics_summary(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project profile metrics not found")
    return AnalyticsEngine.get_project_summary(db, project_id)

@app.get("/api/v1/analytics/velocity/{project_id}")
def get_project_velocity_timeline(project_id: int, days: int = 14, db: Session = Depends(get_db)):
    return AnalyticsEngine.get_velocity_trend(db, project_id, days=days)