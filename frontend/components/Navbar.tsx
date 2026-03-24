"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-2 font-bold text-xl text-brand-700 hover:text-brand-900 transition-colors"
        >
          <span className="text-2xl">⚡</span>
          JobScraper
        </Link>

        <div className="flex items-center gap-1">
          <Link
            href="/jobs"
            className={clsx(
              "px-3 py-2 rounded-md text-sm font-medium transition-colors",
              pathname === "/jobs" || pathname.startsWith("/jobs/")
                ? "bg-brand-50 text-brand-700"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            )}
          >
            Browse Jobs
          </Link>
          <Link
            href="/alerts"
            className={clsx(
              "px-3 py-2 rounded-md text-sm font-medium transition-colors",
              pathname === "/alerts"
                ? "bg-brand-50 text-brand-700"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            )}
          >
            Alerts
          </Link>
          <a
            href="https://github.com/yourname/jobscraper"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-2 px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
          >
            GitHub
          </a>
        </div>
      </div>
    </nav>
  );
}
