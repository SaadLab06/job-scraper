import { Suspense } from "react";
import { SearchBar } from "@/components/SearchBar";
import { JobCard } from "@/components/JobCard";
import { FilterSidebar } from "@/components/FilterSidebar";
import { Pagination } from "@/components/Pagination";
import { searchJobs } from "@/lib/api";
import type { SearchParams } from "@/lib/types";

interface PageProps {
  searchParams: {
    q?: string;
    location?: string;
    job_type?: string;
    experience_level?: string;
    is_remote?: string;
    is_hybrid?: string;
    salary_min?: string;
    salary_max?: string;
    days_ago?: string;
    source?: string;
    page?: string;
    sort_by?: string;
  };
}

async function JobResults({ searchParams }: PageProps) {
  const page = parseInt(searchParams.page ?? "1", 10);
  const pageSize = 20;

  const params: SearchParams = {
    q: searchParams.q,
    location: searchParams.location,
    job_type: searchParams.job_type as SearchParams["job_type"],
    experience_level: searchParams.experience_level as SearchParams["experience_level"],
    is_remote: searchParams.is_remote === "true" ? true : undefined,
    is_hybrid: searchParams.is_hybrid === "true" ? true : undefined,
    salary_min: searchParams.salary_min ? Number(searchParams.salary_min) : undefined,
    salary_max: searchParams.salary_max ? Number(searchParams.salary_max) : undefined,
    days_ago: searchParams.days_ago ? Number(searchParams.days_ago) : undefined,
    source: searchParams.source,
    page,
    page_size: pageSize,
    sort_by: (searchParams.sort_by as SearchParams["sort_by"]) ?? "relevance",
  };

  let result = { jobs: [] as Awaited<ReturnType<typeof searchJobs>>["jobs"], total: 0, page: 1, page_size: pageSize };
  let error: string | null = null;

  try {
    result = await searchJobs(params);
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to fetch jobs";
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <p className="text-5xl mb-4">⚠️</p>
        <p className="text-lg font-medium text-gray-700">Could not connect to API</p>
        <p className="text-sm text-gray-500 mt-1">{error}</p>
        <p className="text-sm text-gray-400 mt-4">
          Make sure the backend is running: <code className="bg-gray-100 px-1 rounded">docker-compose up api</code>
        </p>
      </div>
    );
  }

  if (result.jobs.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-5xl mb-4">🔍</p>
        <p className="text-lg font-medium text-gray-700">No jobs found</p>
        <p className="text-sm text-gray-500 mt-1">Try different keywords or clear some filters.</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        {result.jobs.map((job) => (
          <JobCard key={job.id} job={job} />
        ))}
      </div>
      <Pagination page={result.page} pageSize={result.page_size} total={result.total} />
    </>
  );
}

export default function JobsPage({ searchParams }: PageProps) {
  const hasQuery = searchParams.q || searchParams.location;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Search bar */}
      <div className="mb-6">
        <SearchBar
          defaultKeyword={searchParams.q ?? ""}
          defaultLocation={searchParams.location ?? ""}
        />
      </div>

      {/* Results header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold text-gray-900">
          {hasQuery
            ? `Results for "${searchParams.q ?? searchParams.location}"`
            : "All Jobs"}
        </h1>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span>Sort:</span>
          <a
            href={`/jobs?${new URLSearchParams({ ...searchParams, sort_by: "relevance" }).toString()}`}
            className={
              (searchParams.sort_by ?? "relevance") === "relevance"
                ? "font-semibold text-brand-600"
                : "hover:text-gray-800"
            }
          >
            Relevance
          </a>
          <span>/</span>
          <a
            href={`/jobs?${new URLSearchParams({ ...searchParams, sort_by: "posted_at" }).toString()}`}
            className={
              searchParams.sort_by === "posted_at"
                ? "font-semibold text-brand-600"
                : "hover:text-gray-800"
            }
          >
            Newest
          </a>
        </div>
      </div>

      <div className="flex gap-8">
        {/* Filter sidebar */}
        <div className="hidden lg:block w-56 flex-shrink-0">
          <Suspense>
            <FilterSidebar />
          </Suspense>
        </div>

        {/* Job list */}
        <div className="flex-1 min-w-0">
          <Suspense
            fallback={
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="bg-white rounded-xl border border-gray-200 h-32 animate-pulse" />
                ))}
              </div>
            }
          >
            <JobResults searchParams={searchParams} />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
