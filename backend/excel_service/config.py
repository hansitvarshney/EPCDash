"""
Config schema for the Excel Service Layer.

The whole point of this module: application/workflow code never hardcodes a
sheet name or cell address. It only ever refers to a logical `category`
(DPR / MATERIAL / BILLING / DRAWING) and a logical field name. The actual
sheet/cell layout is resolved from a JSON profile loaded by `registry.py`.

To onboard a real turnkey business's live workbook later, drop a new JSON
profile into `backend/excel_service/templates/` pointing at their template
file and column layout, then flip the `EXCEL_TEMPLATE_PROFILE` env var — zero
code changes required.
"""
from typing import Dict, Optional
from pydantic import BaseModel, Field


class SheetMapping(BaseModel):
    """Describes exactly where one logical data category lives inside a workbook."""

    sheet_name: str
    header_row: int = 1
    data_start_row: int = 2
    # logical field name -> spreadsheet column letter (e.g. "metric_value": "E")
    field_to_column: Dict[str, str]
    # logical metadata key -> single cell reference (e.g. "report_date": "B4")
    metadata_cells: Dict[str, str] = Field(default_factory=dict)


class WorkbookTemplateConfig(BaseModel):
    """A full profile: one physical template workbook + one SheetMapping per category."""

    profile_name: str
    template_path: str
    output_dir: str = "outputs"
    sheets: Dict[str, SheetMapping]

    def sheet_for(self, category: str) -> SheetMapping:
        try:
            return self.sheets[category]
        except KeyError as exc:
            raise KeyError(
                f"No sheet mapping configured for category '{category}' in profile "
                f"'{self.profile_name}'. Configured categories: {list(self.sheets.keys())}"
            ) from exc
