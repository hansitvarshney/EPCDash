# reset_dates.py
from backend.database import SessionLocal, DailySiteLog
from datetime import datetime

db = SessionLocal()
logs = db.query(DailySiteLog).all()

print("Scanning and fixing legacy site logs...")
for log in logs:
    clean = log.report_date.strip().replace("/", "-").replace(".", "-")
    # Matrix of possibilities currently saved
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%y-%m-%d", "%d-%m-%y"):
        try:
            standardized = datetime.strptime(clean, fmt).strftime("%Y-%m-%d")
            if log.report_date != standardized:
                print(f"Fixing format: {log.report_date} -> {standardized}")
                log.report_date = standardized
            break
        except ValueError:
            continue

db.commit()
db.close()
print("Done! All database date fields are now uniformly formatted as YYYY-MM-DD.")