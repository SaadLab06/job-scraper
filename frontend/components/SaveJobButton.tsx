"use client";

import { useSavedJobs } from "@/hooks/useSavedJobs";

export function SaveJobButton({ jobId }: { jobId: string }) {
  const { isSaved, toggleSave } = useSavedJobs();
  const saved = isSaved(jobId);

  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        toggleSave(jobId);
      }}
      aria-label={saved ? "Unsave job" : "Save job"}
      className="flex-shrink-0 text-gray-300 hover:text-yellow-400 transition-colors"
    >
      <svg
        className="w-5 h-5"
        fill={saved ? "currentColor" : "none"}
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={saved ? 0 : 1.5}
        color={saved ? "#f59e0b" : undefined}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z"
        />
      </svg>
    </button>
  );
}
