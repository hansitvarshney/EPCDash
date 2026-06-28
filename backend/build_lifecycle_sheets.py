import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

def init_master_system():
    os.makedirs("templates", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    wb = openpyxl.Workbook()
    
    # --- STYLE CONFIGS ---
    navy_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    green_fill = PatternFill(start_color="36648B", end_color="36648B", fill_type="solid")
    white_bold = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="1F497D")
    
    # SHEET 1: Daily Progress Log Ingestion
    ws1 = wb.active
    ws1.title = "Daily_Progress_Log"
    ws1.views.sheetView[0].showGridLines = True
    ws1["A1"] = "DAILY PROGRESS EXTRACTION LEDGER"
    ws1["A1"].font = title_font
    ws1["A3"] = "Report Date:"
    ws1["B3"] = "YYYY-MM-DD"
    
    headers_log = ["Element ID", "Sub-Tag", "Formula Notation", "Claimed Metric", "Unit", "System Audit Notes"]
    for i, h in enumerate(headers_log, 1):
        cell = ws1.cell(row=5, column=i, value=h)
        cell.font = white_bold; cell.fill = navy_fill; cell.alignment = Alignment(horizontal="center")

    # SHEET 2: Dynamic Material Inventory Balance Sheet
    ws2 = wb.create_sheet(title="Inventory_Reconciliation")
    ws2.views.sheetView[0].showGridLines = True
    ws2["A1"] = "LIVE SITE MATERIAL INVENTORY MONITOR"
    ws2["A1"].font = Font(name="Calibri", size=14, bold=True, color="36648B")
    
    headers_inv = ["Material Description", "Unit", "Opening Balance", "Daily Quantity Used", "Current Remaining Stock"]
    for i, h in enumerate(headers_inv, 1):
        cell = ws2.cell(row=4, column=i, value=h)
        cell.font = white_bold; cell.fill = green_fill; cell.alignment = Alignment(horizontal="center")
        
    # Inject some mock starting inventory balances
    mock_stock = [
        ("20ø Reinforcement Steel", "Kg", 25000),
        ("25ø Reinforcement Steel", "Kg", 18000),
        ("Shuttering Ply Board Panels", "Nos", 1200),
    ]
    for idx, (mat, unit, bal) in enumerate(mock_stock, 5):
        ws2[f"A{idx}"] = mat
        ws2[f"B{idx}"] = unit
        ws2[f"C{idx}"] = bal
        ws2[f"D{idx}"] = 0 # Ingested dynamically
        ws2[f"E{idx}"] = f"=C{idx}-D{idx}" # Excel Formula native calculation!

    # SHEET 3: Schedule Remaining Work Target Tracker
    ws3 = wb.create_sheet(title="Project_Baseline_Tracker")
    ws3.views.sheetView[0].showGridLines = True
    ws3["A1"] = "MASTER SCHEDULE RUNNING TRACKER"
    ws3["A1"].font = title_font
    
    headers_sch = ["Work Activity Scope", "Unit", "Total Project Target (BOQ)", "Cumulative Done to Date", "Work Balance Remaining"]
    for i, h in enumerate(headers_sch, 1):
        cell = ws3.cell(row=4, column=i, value=h)
        cell.font = white_bold; cell.fill = navy_fill; cell.alignment = Alignment(horizontal="center")
        
    ws3["A5"] = "Shear Wall Shuttering Work"
    ws3["B5"] = "m2"
    ws3["C5"] = 5000.00  # Say this is his total project scope requirement
    ws3["D5"] = 1250.40  # Already executed in past days
    ws3["E5"] = "=C5-D5" # Excel native metric
    
    # Adjust widths
    for ws in [ws1, ws2, ws3]:
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 25

    wb.save("templates/master_site_template.xlsx")
    print("🚀 Blueprint Lifecycle System Initialized.")

if __name__ == "__main__":
    init_master_system()