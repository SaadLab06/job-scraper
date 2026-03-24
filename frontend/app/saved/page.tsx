import type { Metadata } from "next";
import { SavedJobsList } from "@/components/SavedJobsList";

export const metadata: Metadata = {
  title: "Saved Jobs — JobScraper",
};

export default function SavedPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Saved Jobs</h1>
      <p className="text-sm text-gray-500 mb-8">
        Jobs you bookmarked — stored locally in your browser.
      </p>
      <SavedJobsList />
    </div>
  );
}
