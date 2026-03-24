import Link from "next/link";
import { SearchBar } from "@/components/SearchBar";
import { JobCard } from "@/components/JobCard";
import { listJobs } from "@/lib/api";

const STATS = [
  { label: "Job Boards", value: "10+" },
  { label: "Active Listings", value: "50K+" },
  { label: "Updated Every", value: "4 hrs" },
  { label: "Always", value: "Free" },
];

const QUICK_SEARCHES = [
  { label: "🌍 Remote Only", href: "/jobs?is_remote=true" },
  { label: "🐍 Python", href: "/jobs?q=python" },
  { label: "⚛️ React", href: "/jobs?q=react" },
  { label: "🤖 AI / ML", href: "/jobs?q=machine+learning" },
  { label: "📱 Mobile", href: "/jobs?q=ios+android" },
  { label: "🎓 Internships", href: "/jobs?job_type=internship" },
  { label: "📋 Today", href: "/jobs?days_ago=1" },
];

export default async function HomePage() {
  // Fetch a few recent jobs for the preview section
  let recentJobs: Awaited<ReturnType<typeof listJobs>>["jobs"] = [];
  try {
    const data = await listJobs({ page: 1, page_size: 6 });
    recentJobs = data.jobs;
  } catch {
    // API may not be running locally — show empty state
  }

  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-brand-900 via-brand-700 to-brand-500 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-28 flex flex-col items-center text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight mb-4">
            Every job.{" "}
            <span className="text-yellow-300">One place.</span>
            <br />
            Always fresh.
          </h1>
          <p className="text-lg sm:text-xl text-blue-100 max-w-2xl mb-10">
            JobScraper aggregates listings from Greenhouse, Lever, Indeed, LinkedIn, Bayt
            and more — deduplicated, normalized, and searchable in seconds.
          </p>

          <SearchBar size="lg" />

          {/* Quick searches */}
          <div className="flex flex-wrap justify-center gap-2 mt-6">
            {QUICK_SEARCHES.map((qs) => (
              <Link
                key={qs.href}
                href={qs.href}
                className="text-sm bg-white/10 hover:bg-white/20 border border-white/20 text-white rounded-full px-3 py-1 transition-colors"
              >
                {qs.label}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 grid grid-cols-2 sm:grid-cols-4 gap-8">
          {STATS.map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-3xl font-extrabold text-brand-600">{s.value}</p>
              <p className="text-sm text-gray-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Recent Jobs */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Latest Listings</h2>
          <Link
            href="/jobs"
            className="text-sm font-medium text-brand-600 hover:text-brand-700 transition-colors"
          >
            Browse all →
          </Link>
        </div>

        {recentJobs.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            <p className="text-5xl mb-4">🔍</p>
            <p className="text-lg font-medium">No jobs indexed yet.</p>
            <p className="text-sm mt-1">
              Run a scraper with{" "}
              <code className="bg-gray-100 px-1 rounded">
                docker-compose exec worker celery -A workers.celery_app call workers.tasks.run_scraper
                --args=&apos;[&quot;greenhouse&quot;]&apos;
              </code>
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recentJobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        )}
      </section>

      {/* Alert CTA */}
      <section className="bg-brand-50 border-t border-brand-100">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-brand-900 mb-3">
            Never miss your dream job
          </h2>
          <p className="text-gray-600 mb-8 max-w-lg mx-auto">
            Set up a free email alert for any search query. Get notified the moment a matching
            job is scraped — no account required.
          </p>
          <Link
            href="/alerts"
            className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold px-8 py-3.5 rounded-lg transition-colors text-base"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            Create Free Alert
          </Link>
        </div>
      </section>
    </div>
  );
}
