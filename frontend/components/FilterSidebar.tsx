"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback } from "react";

const JOB_TYPES = [
  { value: "full_time", label: "Full-time" },
  { value: "part_time", label: "Part-time" },
  { value: "contract", label: "Contract" },
  { value: "freelance", label: "Freelance" },
  { value: "internship", label: "Internship" },
];

const EXPERIENCE_LEVELS = [
  { value: "entry", label: "Entry Level" },
  { value: "mid", label: "Mid Level" },
  { value: "senior", label: "Senior" },
  { value: "lead", label: "Lead / Manager" },
];

const DATE_POSTED = [
  { value: "1", label: "Last 24 hours" },
  { value: "3", label: "Last 3 days" },
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" },
];

const SOURCES = [
  { value: "greenhouse", label: "Greenhouse" },
  { value: "lever", label: "Lever" },
  { value: "indeed", label: "Indeed" },
  { value: "indeed_uk", label: "Indeed UK" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "bayt", label: "Bayt" },
  { value: "emploitic", label: "Emploitic" },
  { value: "rekrute", label: "Rekrute" },
];

export function FilterSidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const updateParam = useCallback(
    (key: string, value: string | null) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value === null || value === "") {
        params.delete(key);
      } else {
        params.set(key, value);
      }
      params.delete("page"); // reset pagination on filter change
      router.push(`${pathname}?${params.toString()}`);
    },
    [router, pathname, searchParams]
  );

  const toggleBool = useCallback(
    (key: string) => {
      const current = searchParams.get(key);
      updateParam(key, current === "true" ? null : "true");
    },
    [searchParams, updateParam]
  );

  const clearAll = useCallback(() => {
    const q = searchParams.get("q");
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    router.push(`${pathname}?${params.toString()}`);
  }, [router, pathname, searchParams]);

  const hasFilters = [
    "job_type",
    "experience_level",
    "is_remote",
    "is_hybrid",
    "days_ago",
    "source",
    "salary_min",
    "salary_max",
  ].some((k) => searchParams.has(k));

  function FilterCheckbox({
    paramKey,
    value,
    label,
  }: {
    paramKey: string;
    value: string;
    label: string;
  }) {
    const checked = searchParams.get(paramKey) === value;
    return (
      <label className="flex items-center gap-2 cursor-pointer group">
        <input
          type="radio"
          name={paramKey}
          checked={checked}
          onChange={() => updateParam(paramKey, checked ? null : value)}
          className="accent-brand-600"
        />
        <span className="text-sm text-gray-700 group-hover:text-gray-900">{label}</span>
      </label>
    );
  }

  return (
    <aside className="w-full space-y-6">
      {hasFilters && (
        <button
          onClick={clearAll}
          className="text-xs font-medium text-red-600 hover:text-red-700 transition-colors"
        >
          ✕ Clear all filters
        </button>
      )}

      {/* Work mode */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
          Work Mode
        </h3>
        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              checked={searchParams.get("is_remote") === "true"}
              onChange={() => toggleBool("is_remote")}
              className="accent-brand-600"
            />
            <span className="text-sm text-gray-700 group-hover:text-gray-900">Remote</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              checked={searchParams.get("is_hybrid") === "true"}
              onChange={() => toggleBool("is_hybrid")}
              className="accent-brand-600"
            />
            <span className="text-sm text-gray-700 group-hover:text-gray-900">Hybrid</span>
          </label>
        </div>
      </div>

      {/* Job Type */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
          Job Type
        </h3>
        <div className="space-y-2">
          {JOB_TYPES.map((jt) => (
            <FilterCheckbox key={jt.value} paramKey="job_type" value={jt.value} label={jt.label} />
          ))}
        </div>
      </div>

      {/* Experience Level */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
          Experience
        </h3>
        <div className="space-y-2">
          {EXPERIENCE_LEVELS.map((el) => (
            <FilterCheckbox
              key={el.value}
              paramKey="experience_level"
              value={el.value}
              label={el.label}
            />
          ))}
        </div>
      </div>

      {/* Date Posted */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
          Date Posted
        </h3>
        <div className="space-y-2">
          {DATE_POSTED.map((dp) => (
            <FilterCheckbox
              key={dp.value}
              paramKey="days_ago"
              value={dp.value}
              label={dp.label}
            />
          ))}
        </div>
      </div>

      {/* Salary */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
          Salary (USD)
        </h3>
        <div className="flex gap-2">
          <input
            type="number"
            placeholder="Min"
            value={searchParams.get("salary_min") ?? ""}
            onChange={(e) => updateParam("salary_min", e.target.value || null)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <input
            type="number"
            placeholder="Max"
            value={searchParams.get("salary_max") ?? ""}
            onChange={(e) => updateParam("salary_max", e.target.value || null)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
      </div>

      {/* Source */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
          Source Board
        </h3>
        <div className="space-y-2">
          {SOURCES.map((s) => (
            <FilterCheckbox key={s.value} paramKey="source" value={s.value} label={s.label} />
          ))}
        </div>
      </div>
    </aside>
  );
}
