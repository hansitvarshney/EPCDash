const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export type HealthStatus = 'ON_TRACK' | 'AT_RISK' | 'ACTION_REQUIRED';

export interface OpenExceptionCounts {
  critical: number;
  warning: number;
  info: number;
}

export interface SiteCard {
  id: number;
  name: string;
  location: string | null;
  client_name: string | null;
  health_status: HealthStatus;
  open_exceptions: OpenExceptionCounts;
  last_synced_date: string | null;
  total_tender_value: number;
}

export interface SiteDetail {
  id: number;
  name: string;
  location: string | null;
  client_name: string | null;
  contract_value: number | null;
  start_date: string | null;
  target_end_date: string | null;
  health_status: HealthStatus;
}

export interface ManpowerDeployed {
  cumulative_masons: number;
  cumulative_helpers: number;
  total_man_days: number;
}

export interface QuantityExecuted {
  category: string;
  element_id: string;
  total_output: number;
  unit: string;
}

export interface ProjectSummary {
  project_id: number;
  active_log_dates: string[];
  manpower_deployed: ManpowerDeployed;
  quantities_executed: QuantityExecuted[];
}

export interface VelocitySeriesPoint {
  report_date: string;
  actual_progress_pct: number;
}

export interface VelocityData {
  project_id: number;
  schedule_baseline_pct: number | null;
  latest_actual_progress_pct: number | null;
  series: VelocitySeriesPoint[];
}

export interface ContractTimeline {
  start_date: string | null;
  target_end_date: string | null;
  contract_value: number | null;
  total_days: number | null;
  days_elapsed: number | null;
  days_remaining: number | null;
  pct_elapsed: number | null;
  is_overdue: boolean;
}

export interface TenderInvoicedRate {
  contract_value: number | null;
  invoiced_amount: number;
  invoiced_pct: number | null;
}

export interface UninvoicedWorkValue {
  contract_value: number | null;
  uninvoiced_amount: number;
  uninvoiced_pct: number | null;
}

export interface MaterialVariance {
  materials_over_allocated: number;
  worst_material_name: string | null;
  worst_variance_pct: number | null;
}

export interface OperationalMetrics {
  tender_invoiced_rate: TenderInvoicedRate;
  uninvoiced_work_value: UninvoicedWorkValue;
  material_variance: MaterialVariance;
}

export interface SiteOverview {
  site: {
    id: number;
    name: string;
    location: string | null;
    client_name: string | null;
    health_status: HealthStatus;
    start_date: string | null;
    target_end_date: string | null;
    contract_value: number | null;
  };
  summary: ProjectSummary;
  velocity: VelocityData;
  open_exceptions: OpenExceptionCounts;
  contract_timeline: ContractTimeline;
  operational_metrics: OperationalMetrics;
}

export interface AttendanceEntry {
  contractor_name: string;
  crew_type: string;
  masons_count: number;
  helpers_count: number;
  assigned_activity: string | null;
}

export interface AttendanceDayTotals {
  masons: number;
  helpers: number;
  total: number;
}

export interface HistoricalDailyTotal {
  report_date: string;
  masons_count: number;
  helpers_count: number;
  total_man_days: number;
}

export interface AttendanceSheet {
  current_date: string | null;
  current_day_entries: AttendanceEntry[];
  current_day_totals: AttendanceDayTotals;
  historical_daily_totals: HistoricalDailyTotal[];
}

export type ExceptionSeverity = 'INFO' | 'WARNING' | 'CRITICAL';
export type ExceptionCategory = 'DPR' | 'MATERIAL' | 'BILLING' | 'DRAWING' | 'SCHEDULE';

export interface SourceCitation {
  document_name: string | null;
  page_number: number | null;
  text_snippet: string | null;
}

export interface ExceptionAlert {
  id: number;
  category: ExceptionCategory;
  severity: ExceptionSeverity;
  message: string;
  related_table: string | null;
  related_record_id: number | null;
  is_resolved: boolean;
  created_at: string | null;
  source_citation: SourceCitation;
}

export interface DownloadFile {
  document_id: number;
  file_name: string;
  category: string;
  report_date: string | null;
  last_synced_at: string;
  size_bytes: number;
  download_url: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
}

export interface CompletedMilestone {
  milestone_name: string;
  target_date: string | null;
  sequence: number;
}

export interface NextMilestone {
  milestone_name: string;
  target_date: string | null;
  days_left: number | null;
}

export interface AllMilestoneRow {
  id: number;
  milestone_name: string;
  target_date: string | null;
  status: 'PENDING' | 'COMPLETED';
}

export interface PaymentMilestoneRow {
  id: number;
  bill_name: string;
  contract_pct: number;
  bill_amount: number;
  status: 'LOCKED' | 'ELIGIBLE' | 'INVOICED' | 'PAID';
  linked_physical_milestone_name: string | null;
  eligible_at: string | null;
  invoiced_at: string | null;
  paid_at: string | null;
}

export interface MilestoneTracker {
  completed_milestones: CompletedMilestone[];
  completed_count: number;
  total_count: number;
  next_milestone: NextMilestone | null;
  all_milestones: AllMilestoneRow[];
  is_lagging_schedule: boolean;
  schedule_baseline_pct: number | null;
  latest_actual_progress_pct: number | null;
  payment_milestones: PaymentMilestoneRow[];
}

export interface MaterialVelocityRow {
  material_name: string;
  unit: string;
  consumed_yesterday: number;
  consumed_till_now: number;
  design_specified_qty: number;
  pct_of_boq: number | null;
}

export interface BillingActivityRow {
  vendor_name: string;
  invoice_number: string | null;
  invoice_date: string | null;
  invoice_amount: number;
  status: string;
}

export interface DailyExpenseLog {
  report_date: string;
  labor_wages_paid: number;
  misc_expenses_paid: number;
  misc_expenses_notes: string | null;
  source: string;
}

export interface FinancialLedger {
  total_invested_till_now: number;
  projected_total_to_completion: number;
  contract_value: number | null;
  pct_of_contract_invested: number | null;
  total_manual_daily_expenses: number;
  total_active_penalties: number;
  estimated_profit: number | null;
  todays_expense_log: DailyExpenseLog | null;
}

export interface DrawingStatusRow {
  drawing_number: string;
  drawing_title: string | null;
  discipline: string | null;
  gfc_revision: string | null;
  gfc_issue_date: string | null;
  client_signoff_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  client_signoff_date: string | null;
}

export interface SiteInsights {
  milestone_tracker: MilestoneTracker;
  material_velocity: MaterialVelocityRow[];
  latest_billing_activity: BillingActivityRow[];
  financial_ledger: FinancialLedger;
  drawing_status_ledger: DrawingStatusRow[];
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore body parse failure
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function fetchSites(): Promise<SiteCard[]> {
  const res = await fetch(`${BASE_URL}/api/v1/sites`, { cache: 'no-store' });
  return handle<SiteCard[]>(res);
}

export async function fetchSite(siteId: number): Promise<SiteDetail> {
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}`, { cache: 'no-store' });
  return handle<SiteDetail>(res);
}

export async function fetchSiteOverview(siteId: number): Promise<SiteOverview> {
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/overview`, { cache: 'no-store' });
  return handle<SiteOverview>(res);
}

export async function fetchAttendance(siteId: number): Promise<AttendanceSheet> {
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/attendance`, { cache: 'no-store' });
  return handle<AttendanceSheet>(res);
}

export function attendanceExportUrl(siteId: number): string {
  return `${BASE_URL}/api/v1/sites/${siteId}/attendance/export`;
}

export async function fetchSiteInsights(siteId: number): Promise<SiteInsights> {
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/insights`, { cache: 'no-store' });
  return handle<SiteInsights>(res);
}

export async function saveDailyExpenseLog(
  siteId: number,
  payload: { labor_wages_paid?: number; misc_expenses_paid?: number; misc_expenses_notes?: string }
): Promise<DailyExpenseLog> {
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/expenses`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handle<DailyExpenseLog>(res);
}

export async function updateMilestoneStatus(
  siteId: number,
  milestoneId: number,
  status: 'PENDING' | 'COMPLETED'
): Promise<{ id: number; milestone_name: string; status: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/milestones/${milestoneId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  return handle(res);
}

export async function updatePaymentMilestoneStatus(
  siteId: number,
  paymentMilestoneId: number,
  status: 'INVOICED' | 'PAID'
): Promise<{ id: number; bill_name: string; status: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/payment-milestones/${paymentMilestoneId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  return handle(res);
}

export async function fetchExceptions(siteId: number, includeResolved = false): Promise<ExceptionAlert[]> {
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/exceptions?include_resolved=${includeResolved}`, { cache: 'no-store' });
  return handle<ExceptionAlert[]>(res);
}

export async function resolveException(siteId: number, exceptionId: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/exceptions/${exceptionId}/resolve`, { method: 'POST' });
  await handle(res);
}

export async function fetchDownloads(siteId: number): Promise<DownloadFile[]> {
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/downloads`, { cache: 'no-store' });
  return handle<DownloadFile[]>(res);
}

export function downloadFileUrl(downloadUrl: string): string {
  return `${BASE_URL}${downloadUrl}`;
}

export async function deleteDocument(siteId: number, documentId: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/documents/${documentId}`, { method: 'DELETE' });
  await handle(res);
}

export interface IngestCategoryResult {
  category: string;
  status: 'success' | 'error';
  document_id?: number;
  excel_output_path?: string;
  exceptions_raised?: number;
  error?: string;
}

export interface IngestResponse {
  status: 'success' | 'partial_success' | 'error';
  file_names: string[];
  page_count: number;
  results: IngestCategoryResult[];
}

export async function ingestDocument(siteId: number, categories: string[], files: File[]): Promise<IngestResponse> {
  const formData = new FormData();
  categories.forEach((category) => formData.append('categories', category));
  files.forEach((file) => formData.append('files', file));
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/ingest`, { method: 'POST', body: formData });
  return handle<IngestResponse>(res);
}

export async function uploadReferenceDocument(siteId: number, file: File): Promise<{ status: string; file_name: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/documents`, { method: 'POST', body: formData });
  return handle(res);
}

export async function sendChatMessage(siteId: number, question: string): Promise<{ response: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/sites/${siteId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  return handle(res);
}
