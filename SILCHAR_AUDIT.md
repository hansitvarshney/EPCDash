# Silchar Site Contract Audit & Feature Recommendations

**Project:** Construction of Integrated Deputy Commissioner Office for Cachar at Silchar, Assam (EPC Mode-1)
**Contract Value:** Rs. 41,44,06,450.00
**Duration:** 30 Months

Based on a comprehensive review of the 300-page `I. SBD.pdf` tender agreement, the following critical operational trackers, risk clauses, and compliance gates have been identified. These are essential for an EPC contracting firm to monitor and are recommended for inclusion in the next sprint of the Operational Cockpit.

## 1. Mobilization Advance Tracker
*   **Contract Clause:** The contract allows a 10% mobilization advance and a 5% plant/machinery advance. Crucially, installments (except the first) are released *only* after receiving a utilization certificate supported by a bank statement showing the disbursement of the advance.
*   **Operational Risk:** Failure to provide timely utilization proofs will block subsequent cash flow and delay project mobilization.
*   **Dashboard Recommendation:** **"Mobilization Advance Ledger"**
    *   *Visualization:* A progress bar showing Total Advance Available vs. Disbursed vs. Utilized.
    *   *Actionable Insight:* Alerts when utilization drops below the threshold required to trigger the next installment release.

## 2. Defect Liability Period (DLP) Monitor
*   **Contract Clause:** A 12-month Defect Liability Period (DLP) is mandated post-completion. The contractor must attend to minor complaints within 24 hours and major complaints within 3 days. Failure to do so allows the department to rectify at the contractor's cost.
*   **Operational Risk:** SLA breaches during DLP directly impact the release of the final retention money/security deposit and incur third-party rectification costs.
*   **Dashboard Recommendation:** **"DLP Ticketing Module"**
    *   *Visualization:* A Kanban-style or list view of open snags/complaints categorized by Minor/Major.
    *   *Actionable Insight:* Countdown timers (24h/72h) for each ticket, turning red when SLAs are breached, triggering immediate executive escalation.

## 3. Compliance & Penalty Gates
*   **Contract Clauses:** 
    *   Rs. 500/day penalty for non-compliance/delay in opening a separate bank account for labor payments.
    *   Rs. 500/trip penalty for improper dumping of construction materials on metalled roads.
    *   Various other penalties under Clause 19 (C, D, G) ranging from Rs. 400 to Rs. 2500 per default for labor law violations.
*   **Operational Risk:** These "micro-penalties" can accumulate silently and be deducted abruptly from R/A bills, impacting margins.
*   **Dashboard Recommendation:** **"Compliance & EHS Penalty Log"**
    *   *Visualization:* A running ticker or ledger of accrued penalties, integrated directly into the existing "Critical Exceptions Feed".
    *   *Actionable Insight:* Real-time visibility into EHS/Compliance deductions before they are formalized in the monthly billing cycle.

## 4. Quality Assurance (Site Lab) Log
*   **Contract Clause:** The contractor is required to establish a site laboratory equipped with specific testing machinery (e.g., 100MT compression testing machine, slump cone, Vicat apparatus).
*   **Operational Risk:** Missing concrete cube test results or failed material approvals can halt structural pours or lead to rejected work.
*   **Dashboard Recommendation:** **"Quality Test Register"**
    *   *Visualization:* A matrix tracking mandatory tests (like 7-day and 28-day concrete cube compressive strengths) against pour dates.
    *   *Actionable Insight:* Automated flags for pending test results or tests that fail to meet the IS:456-2000 specified thresholds, preventing subsequent dependent activities.
