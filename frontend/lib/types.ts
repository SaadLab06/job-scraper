export type JobType = "full_time" | "part_time" | "contract" | "freelance" | "internship";
export type ExperienceLevel = "entry" | "mid" | "senior" | "lead";

export interface Job {
  id: string;
  source: string;
  source_id: string | null;
  url: string;
  title: string;
  company: string;
  company_logo: string | null;
  location: string | null;
  lat: number | null;
  lng: number | null;
  is_remote: boolean;
  is_hybrid: boolean;
  job_type: JobType | null;
  experience_level: ExperienceLevel | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  description: string | null;
  skills: string[];
  posted_at: string | null;
  scraped_at: string;
  is_active: boolean;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  page: number;
  page_size: number;
}

export interface SearchParams {
  q?: string;
  location?: string;
  job_type?: JobType;
  experience_level?: ExperienceLevel;
  is_remote?: boolean;
  is_hybrid?: boolean;
  salary_min?: number;
  salary_max?: number;
  days_ago?: number;
  source?: string;
  page?: number;
  page_size?: number;
  sort_by?: "relevance" | "posted_at";
}
