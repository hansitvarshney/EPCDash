const BASE_URL = 'http://localhost:8000';

export interface Project {
  id: number;
  name: string;
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
  manpower_deployed: ManpowerDeployed;
  quantities_executed: QuantityExecuted[];
}

// Fetch all active sites for the selection dropdown
export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${BASE_URL}/projects`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch projects');
  return res.json();
}

// Fetch macro metrics for a specifically selected site
export async function fetchProjectSummary(projectId: number): Promise<ProjectSummary> {
  const res = await fetch(`${BASE_URL}/api/v1/analytics/summary/${projectId}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch project summary');
  return res.json();
}