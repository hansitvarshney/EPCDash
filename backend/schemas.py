from pydantic import BaseModel, Field
from typing import List, Optional

# Copy your actual schema layout variables here
class AdaptiveLayoutConfig:
    DEFAULT_TEMPLATE_PATH = "templates/master_site_template.xlsx"
    METADATA_DATE_CELL = "B3"
    METADATA_CATEGORY_CELL = "B4"
    HAS_LABOR_SECTION = True
    LABOR_ROW_START = 6
    QUANTITY_ROW_START = 18
    
class QuantityEntry(BaseModel):
    category: str
    structural_id: str
    total_output: float
    unit: str
    is_mathematically_correct: bool

class ManpowerEntry(BaseModel):
    cumulative_masons: int
    cumulative_helpers: int
    total_man_days: int

class AdaptiveLifecycleSchema(BaseModel):
    report_date: str
    log_category: str
    quantity_entries: List[QuantityEntry]
    manpower_deployed: ManpowerEntry

class LaborRowEntry(BaseModel):
    contractor_name: str = Field(description="Name of the sub-contractor (e.g., 'Paban Nayak', 'Jehirul Islam')")
    count: int = Field(description="The number of laborers written in the 'No of Labour' column.")
    designation: str = Field(description="Designation code or role character exactly as written: 'Helper', 'H', 'Mason', 'M'.")

class ExtractedQuantityEntry(BaseModel):
    work_category: str = Field(description="Clean executive title conversion (e.g., 'Shear Wall Shuttering').")
    element_id: str = Field(description="The structural tracking node code (e.g., 'SW-4').")
    raw_mathematical_dimensions: List[str] = Field(description="List of raw multi-line calculation text lines.")
    claimed_subtotals_on_paper: List[float] = Field(description="List of written values for each formula line item.")
    unit: str = Field(default="sqm")

class ProductionSiteLogPayload(BaseModel):
    report_date: str = Field(description="Date from the document header formatted as 'YYYY-MM-DD'.")
    log_category: str = Field(default="GENERAL_CIVIL_WORKS")
    # 🎯 Extract row lists rather than pre-calculated integers
    workforce_roster: List[LaborRowEntry] = Field(description="List of all raw rows found in the labor allocation table layout.")
    quantity_entries: List[ExtractedQuantityEntry]    

ADAPTIVE_LIFECYCLE_CONTEXT = """
You are an expert EPC context data extraction model...
"""