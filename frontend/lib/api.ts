import type { Job, JobListResponse, SearchParams } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function buildQuery(params: Record<string, unknown>): string {
  const q = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      q.set(key, String(value));
    }
  }
  return q.toString();
}

export async function searchJobs(params: SearchParams): Promise<JobListResponse> {
  const qs = buildQuery(params as Record<string, unknown>);
  const res = await fetch(`${API_BASE}/api/v1/jobs/search?${qs}`, {
    next: { revalidate: 30 },
  });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

export async function listJobs(params: {
  page?: number;
  page_size?: number;
  source?: string;
  is_remote?: boolean;
}): Promise<JobListResponse> {
  const qs = buildQuery(params as Record<string, unknown>);
  const res = await fetch(`${API_BASE}/api/v1/jobs?${qs}`, {
    next: { revalidate: 30 },
  });
  if (!res.ok) throw new Error(`List jobs failed: ${res.status}`);
  return res.json();
}

export async function getJob(id: string): Promise<Job> {
  const res = await fetch(`${API_BASE}/api/v1/jobs/${id}`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error(`Job not found: ${res.status}`);
  return res.json();
}

export async function createAlert(data: {
  email: string;
  query: string;
  location?: string;
  frequency: "daily" | "weekly";
}): Promise<{ id: string; message: string }> {
  const res = await fetch(`${API_BASE}/api/v1/alerts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Alert creation failed: ${res.status}`);
  return res.json();
}
