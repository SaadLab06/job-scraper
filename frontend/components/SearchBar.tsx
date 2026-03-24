"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

interface SearchBarProps {
  defaultKeyword?: string;
  defaultLocation?: string;
  size?: "lg" | "md";
}

export function SearchBar({
  defaultKeyword = "",
  defaultLocation = "",
  size = "md",
}: SearchBarProps) {
  const router = useRouter();
  const [keyword, setKeyword] = useState(defaultKeyword);
  const [location, setLocation] = useState(defaultLocation);
  const [, startTransition] = useTransition();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (keyword.trim()) params.set("q", keyword.trim());
    if (location.trim()) params.set("location", location.trim());
    startTransition(() => {
      router.push(`/jobs?${params.toString()}`);
    });
  }

  const isLg = size === "lg";

  return (
    <form
      onSubmit={handleSubmit}
      className={`flex flex-col sm:flex-row gap-2 w-full ${isLg ? "max-w-3xl" : "max-w-2xl"}`}
    >
      <div className="relative flex-1">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="Job title, skills, or company..."
          className={`w-full pl-10 pr-4 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent ${
            isLg ? "py-3.5 text-base" : "py-2.5 text-sm"
          }`}
        />
      </div>

      <div className="relative sm:w-56">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        <input
          type="text"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Location or Remote"
          className={`w-full pl-10 pr-4 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent ${
            isLg ? "py-3.5 text-base" : "py-2.5 text-sm"
          }`}
        />
      </div>

      <button
        type="submit"
        className={`bg-brand-600 hover:bg-brand-700 active:bg-brand-800 text-white font-semibold rounded-lg transition-colors whitespace-nowrap ${
          isLg ? "px-8 py-3.5 text-base" : "px-6 py-2.5 text-sm"
        }`}
      >
        Search
      </button>
    </form>
  );
}
