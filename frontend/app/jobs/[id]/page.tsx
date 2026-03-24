import { notFound } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { formatDistanceToNow, format } from "date-fns";
import { getJob } from "@/lib/api";
import { stripHtml } from "@/lib/sanitize";
import { SaveJobButton } from "@/components/SaveJobButton";
import type { Metadata } from "next";

interface PageProps {
  params: { id: string };
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  try {
    const job = await getJob(params.id);
    return {
      title: `${job.title} at ${job.company} — JobScraper`,
      description: job.description
        ? stripHtml(job.description).slice(0, 160)
        : undefined,
    };
  } catch {
    return { title: "Job Not Found — JobScraper" };
  }
}

const JOB_TYPE_LABELS: Record<string, string> = {
  full_time: "Full-time",
  part_time: "Part-time",
  contract: "Contract",
  freelance: "Freelance",
  internship: "Internship",
};

const EXP_LABELS: Record<string, string> = {
  entry: "Entry Level",
  mid: "Mid Level",
  senior: "Senior",
  lead: "Lead / Manager",
};

export default async function JobDetailPage({ params }: PageProps) {
  let job;
  try {
    job = await getJob(params.id);
  } catch {
    notFound();
  }

  const postedAt = job.posted_at
    ? `${formatDistanceToNow(new Date(job.posted_at), { addSuffix: true })} · ${format(new Date(job.posted_at), "MMM d, yyyy")}`
    : null;

  const salaryText = (() => {
    if (!job.salary_min && !job.salary_max) return null;
    const currency = job.salary_currency || "USD";
    const fmt = (n: number) =>
      new Intl.NumberFormat("en-US", {
        style: "currency",
        currency,
        maximumFractionDigits: 0,
      }).format(n);
    if (job.salary_min && job.salary_max)
      return `${fmt(job.salary_min)} – ${fmt(job.salary_max)} / yr`;
    if (job.salary_min) return `From ${fmt(job.salary_min)} / yr`;
    return `Up to ${fmt(job.salary_max!)} / yr`;
  })();

  const descriptionText = job.description ? stripHtml(job.description) : null;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link href="/" className="hover:text-gray-700">
          Home
        </Link>
        <span>/</span>
        <Link href="/jobs" className="hover:text-gray-700">
          Jobs
        </Link>
        <span>/</span>
        <span className="text-gray-900 truncate max-w-xs">{job.title}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main content */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border border-gray-200 p-6 sm:p-8">
            {/* Header */}
            <div className="flex items-start gap-4 mb-6">
              <div className="flex-shrink-0 w-16 h-16 rounded-xl border border-gray-100 bg-gray-50 flex items-center justify-center overflow-hidden">
                {job.company_logo ? (
                  <Image
                    src={job.company_logo}
                    alt={job.company}
                    width={64}
                    height={64}
                    className="object-contain"
                    unoptimized
                  />
                ) : (
                  <span className="text-2xl font-bold text-gray-300">
                    {job.company.charAt(0).toUpperCase()}
                  </span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
                <p className="text-base text-gray-600 mt-1">{job.company}</p>
              </div>
              <SaveJobButton jobId={job.id} />
            </div>

            {/* Tags */}
            <div className="flex flex-wrap gap-2 mb-6">
              {job.location && (
                <span className="text-sm text-gray-600 flex items-center gap-1 bg-gray-100 rounded-full px-3 py-1">
                  📍 {job.location}
                </span>
              )}
              {job.is_remote && (
                <span className="text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-full px-3 py-1">
                  Remote
                </span>
              )}
              {job.is_hybrid && !job.is_remote && (
                <span className="text-sm font-medium text-purple-700 bg-purple-50 border border-purple-200 rounded-full px-3 py-1">
                  Hybrid
                </span>
              )}
              {job.job_type && (
                <span className="text-sm text-gray-600 bg-gray-100 rounded-full px-3 py-1">
                  {JOB_TYPE_LABELS[job.job_type] ?? job.job_type}
                </span>
              )}
              {job.experience_level && (
                <span className="text-sm text-gray-600 bg-gray-100 rounded-full px-3 py-1">
                  {EXP_LABELS[job.experience_level] ?? job.experience_level}
                </span>
              )}
              {salaryText && (
                <span className="text-sm font-medium text-green-700 bg-green-50 border border-green-200 rounded-full px-3 py-1">
                  💰 {salaryText}
                </span>
              )}
            </div>

            {/* Skills */}
            {job.skills && job.skills.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Required Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {job.skills.map((skill) => (
                    <Link
                      key={skill}
                      href={`/jobs?q=${encodeURIComponent(skill)}`}
                      className="text-xs font-medium text-brand-700 bg-brand-50 border border-brand-200 rounded-full px-2.5 py-1 hover:bg-brand-100 transition-colors"
                    >
                      {skill}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Description — rendered as safe plain text */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Description</h2>
              {descriptionText ? (
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {descriptionText}
                </p>
              ) : (
                <p className="text-gray-500 italic text-sm">No description available.</p>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Apply card */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 sticky top-20">
            <h3 className="font-semibold text-gray-900 mb-4">Apply for this role</h3>
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full text-center bg-brand-600 hover:bg-brand-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Apply on {job.source.charAt(0).toUpperCase() + job.source.slice(1)} →
            </a>
            <p className="text-xs text-gray-400 text-center mt-3">Opens the original posting</p>

            {/* Meta */}
            <div className="mt-6 space-y-3 border-t border-gray-100 pt-4">
              {postedAt && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Posted</span>
                  <span className="text-gray-700 font-medium text-right">{postedAt}</span>
                </div>
              )}
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Source</span>
                <span className="text-gray-700 font-medium capitalize">{job.source}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Status</span>
                <span className={`font-medium ${job.is_active ? "text-green-600" : "text-red-500"}`}>
                  {job.is_active ? "Active" : "Expired"}
                </span>
              </div>
            </div>
          </div>

          {/* Alert CTA */}
          <div className="bg-brand-50 border border-brand-100 rounded-xl p-5">
            <p className="text-sm font-semibold text-brand-900 mb-2">
              Get alerts for similar jobs
            </p>
            <p className="text-xs text-brand-700 mb-3">
              Be notified when new <strong>{job.title}</strong> roles are scraped.
            </p>
            <Link
              href={`/alerts?q=${encodeURIComponent(job.title)}`}
              className="block text-center text-xs font-semibold text-brand-600 border border-brand-300 rounded-lg py-2 hover:bg-brand-100 transition-colors"
            >
              Create Alert →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
