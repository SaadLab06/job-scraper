"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSavedJobs } from "@/hooks/useSavedJobs";
import { JobCard } from "@/components/JobCard";
import type { Job } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function SavedJobsList() {
  const { savedIds, toggleSave } = useSavedJobs();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (savedIds.size === 0) {
      setJobs([]);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);

    Promise.all(
      [...savedIds].map((id) =>
        fetch(`${API_BASE}/api/v1/jobs/${id}`)
          .then((r) => (r.ok ? (r.json() as Promise<Job>) : null))
          .catch(() => null)
      )
    ).then((results) => {
      if (!cancelled) {
        setJobs(results.filter((j): j is Job => j !== null));
        setLoading(false);
      }
    });

    return () => { cancelled = true; };
  }, [savedIds]);

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-200 h-28 animate-pulse" />
        ))}
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-20 text-gray-400">
        <p className="text-5xl mb-4">🔖</p>
        <p className="text-lg font-medium">No saved jobs yet</p>
        <p className="text-sm mt-1">
          Click the bookmark icon on any job card to save it here.
        </p>
        <Link
          href="/jobs"
          className="inline-block mt-6 text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          Browse Jobs →
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} />
      ))}
    </div>
  );
}
