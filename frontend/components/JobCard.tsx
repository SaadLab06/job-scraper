import Link from "next/link";
import Image from "next/image";
import { formatDistanceToNow } from "date-fns";
import clsx from "clsx";
import type { Job } from "@/lib/types";
import { SaveJobButton } from "./SaveJobButton";

const SOURCE_LABELS: Record<string, string> = {
  greenhouse: "Greenhouse",
  lever: "Lever",
  indeed: "Indeed",
  indeed_uk: "Indeed UK",
  linkedin: "LinkedIn",
  bayt: "Bayt",
  emploitic: "Emploitic",
  rekrute: "Rekrute",
};

const JOB_TYPE_LABELS: Record<string, string> = {
  full_time: "Full-time",
  part_time: "Part-time",
  contract: "Contract",
  freelance: "Freelance",
  internship: "Internship",
};

function SalaryBadge({ job }: { job: Job }) {
  if (!job.salary_min && !job.salary_max) return null;
  const currency = job.salary_currency || "USD";
  const fmt = (n: number) =>
    new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(n);
  const text =
    job.salary_min && job.salary_max
      ? `${fmt(job.salary_min)} – ${fmt(job.salary_max)}`
      : job.salary_min
      ? `From ${fmt(job.salary_min)}`
      : `Up to ${fmt(job.salary_max!)}`;
  return (
    <span className="text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded-full px-2 py-0.5">
      {text}
    </span>
  );
}

export function JobCard({ job }: { job: Job }) {
  const postedAt = job.posted_at
    ? formatDistanceToNow(new Date(job.posted_at), { addSuffix: true })
    : null;

  return (
    <div className="group bg-white rounded-xl border border-gray-200 hover:border-brand-300 hover:shadow-md transition-all p-5 flex gap-4">
      {/* Logo */}
      <div className="flex-shrink-0 w-12 h-12 rounded-lg border border-gray-100 bg-gray-50 flex items-center justify-center overflow-hidden">
        {job.company_logo ? (
          <Image
            src={job.company_logo}
            alt={job.company}
            width={48}
            height={48}
            className="object-contain"
            unoptimized
          />
        ) : (
          <span className="text-xl font-bold text-gray-300">
            {job.company.charAt(0).toUpperCase()}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <Link
              href={`/jobs/${job.id}`}
              className="font-semibold text-gray-900 hover:text-brand-600 transition-colors line-clamp-1 group-hover:text-brand-600"
            >
              {job.title}
            </Link>
            <p className="text-sm text-gray-600 mt-0.5">{job.company}</p>
          </div>
          <SaveJobButton jobId={job.id} />
        </div>

        {/* Meta */}
        <div className="flex flex-wrap items-center gap-2 mt-2">
          {job.location && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {job.location}
            </span>
          )}
          {job.is_remote && (
            <span className="text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-full px-2 py-0.5">
              Remote
            </span>
          )}
          {job.is_hybrid && !job.is_remote && (
            <span className="text-xs font-medium text-purple-700 bg-purple-50 border border-purple-200 rounded-full px-2 py-0.5">
              Hybrid
            </span>
          )}
          {job.job_type && (
            <span className="text-xs text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">
              {JOB_TYPE_LABELS[job.job_type] ?? job.job_type}
            </span>
          )}
          <SalaryBadge job={job} />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center gap-2">
            {postedAt && (
              <span className="text-xs text-gray-400">{postedAt}</span>
            )}
            <span
              className={clsx(
                "text-xs font-medium rounded-full px-2 py-0.5 border",
                "text-gray-500 bg-gray-50 border-gray-200"
              )}
            >
              {SOURCE_LABELS[job.source] ?? job.source}
            </span>
          </div>
          <Link
            href={`/jobs/${job.id}`}
            className="text-xs font-medium text-brand-600 hover:text-brand-700 transition-colors"
          >
            View →
          </Link>
        </div>
      </div>
    </div>
  );
}
