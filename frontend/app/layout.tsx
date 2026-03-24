import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "JobScraper — Every job. One place. Always fresh.",
  description:
    "Search thousands of jobs from 10+ boards in one place. Get instant alerts for new matches.",
  openGraph: {
    title: "JobScraper",
    description: "Every job. One place. Always fresh.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-gray-50">
        <Navbar />
        <main className="flex-1">{children}</main>
        <footer className="border-t border-gray-200 bg-white py-6 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row justify-between items-center gap-2 text-sm text-gray-500">
            <span>© {new Date().getFullYear()} JobScraper — Open Source</span>
            <div className="flex gap-4">
              <a
                href="https://github.com/yourname/jobscraper"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-gray-800 transition-colors"
              >
                GitHub
              </a>
              <a href="/api/v1/feeds/rss" className="hover:text-gray-800 transition-colors">
                RSS
              </a>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
