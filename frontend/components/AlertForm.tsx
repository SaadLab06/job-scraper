"use client";

import { useState } from "react";
import { createAlert } from "@/lib/api";

interface AlertFormProps {
  defaultQuery?: string;
  defaultLocation?: string;
}

export function AlertForm({ defaultQuery = "", defaultLocation = "" }: AlertFormProps) {
  const [email, setEmail] = useState("");
  const [query, setQuery] = useState(defaultQuery);
  const [location, setLocation] = useState(defaultLocation);
  const [frequency, setFrequency] = useState<"daily" | "weekly">("daily");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setErrorMsg("");
    try {
      await createAlert({ email, query, location: location || undefined, frequency });
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrorMsg(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  if (status === "success") {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
        <div className="text-4xl mb-3">✅</div>
        <h2 className="text-lg font-semibold text-green-900">Almost there!</h2>
        <p className="text-sm text-green-800 mt-2">
          We sent a confirmation email to <strong>{email}</strong>.
          Click the link inside to activate your alert.
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-xl border border-gray-200 p-6 sm:p-8 space-y-5"
    >
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
          Email address <span className="text-red-500">*</span>
        </label>
        <input
          id="email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
      </div>

      <div>
        <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-1.5">
          Search query <span className="text-red-500">*</span>
        </label>
        <input
          id="query"
          type="text"
          required
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Python developer, React engineer, Data scientist"
          className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
      </div>

      <div>
        <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1.5">
          Location (optional)
        </label>
        <input
          id="location"
          type="text"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="e.g. Remote, Paris, London"
          className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
      </div>

      <div>
        <p className="block text-sm font-medium text-gray-700 mb-1.5">Alert frequency</p>
        <div className="flex gap-3">
          {(["daily", "weekly"] as const).map((f) => (
            <label
              key={f}
              className={`flex-1 flex items-center justify-center gap-2 border rounded-lg px-4 py-2.5 cursor-pointer text-sm transition-colors ${
                frequency === f
                  ? "border-brand-500 bg-brand-50 text-brand-700 font-medium"
                  : "border-gray-300 text-gray-600 hover:border-gray-400"
              }`}
            >
              <input
                type="radio"
                name="frequency"
                value={f}
                checked={frequency === f}
                onChange={() => setFrequency(f)}
                className="sr-only"
              />
              {f === "daily" ? "📅 Daily digest" : "📆 Weekly digest"}
            </label>
          ))}
        </div>
      </div>

      {status === "error" && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">
          {errorMsg}
        </p>
      )}

      <button
        type="submit"
        disabled={status === "loading"}
        className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-semibold py-3 rounded-lg transition-colors"
      >
        {status === "loading" ? "Creating alert…" : "Create Alert →"}
      </button>
    </form>
  );
}
