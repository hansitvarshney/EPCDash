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
  total_po_value: number;
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

export interface SiteOverview {
  site: {
    id: number;
    name: string;
    location: string | null;
    client_name: string | null;
    health_status: HealthStatus;
  };
  summary: ProjectSummary;
  velocity: VelocityData;
  open_exceptions: OpenExceptionCounts;
}

export type ExceptionSeverity = 'INFO' | 'WARNING' | 'CRITICAL';
export type ExceptionCategory = 'DPR' | 'MATERIAL' | 'BILLING' | 'DRAWING';

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
