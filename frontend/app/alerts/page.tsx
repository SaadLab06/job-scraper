import { AlertForm } from "@/components/AlertForm";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Job Alerts — JobScraper",
  description: "Get email notifications when new jobs matching your search are scraped.",
};

interface PageProps {
  searchParams: { q?: string; location?: string };
}

export default function AlertsPage({ searchParams }: PageProps) {
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div className="text-center mb-10">
        <div className="text-5xl mb-4">🔔</div>
        <h1 className="text-3xl font-bold text-gray-900">Job Alerts</h1>
        <p className="text-gray-600 mt-3 max-w-lg mx-auto">
          Subscribe to any search query and receive an email when new matching jobs are scraped.
          No account required — just your email.
        </p>
      </div>

      <AlertForm defaultQuery={searchParams.q} defaultLocation={searchParams.location} />

      <div className="mt-8 bg-gray-50 rounded-xl border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-3">How it works</h3>
        <ol className="space-y-2 text-sm text-gray-600 list-decimal list-inside">
          <li>Enter a search query (e.g. &ldquo;Python developer remote&rdquo;)</li>
          <li>Check your email for a confirmation link</li>
          <li>Click the link to activate your alert</li>
          <li>Receive emails whenever new matching jobs are scraped</li>
        </ol>
        <p className="text-xs text-gray-400 mt-4">
          Unsubscribe anytime from the link in any alert email.
        </p>
      </div>
    </div>
  );
}
