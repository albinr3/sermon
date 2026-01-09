"use client";

import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import Link from "next/link";

import { listSermons } from "../../lib/api";

const POLL_INTERVAL_MS = 3000;
const ACTIVE_STATUSES = new Set(["pending", "uploaded", "processing"]);
const LOADING_ROWS = 3;

const UploadSermon = dynamic(() => import("../components/UploadSermon"), {
  loading: () => (
    <div className="h-10 w-40 animate-pulse rounded-xl bg-slate-900" />
  )
});

const formatStatus = (status) => {
  if (!status) return "Unknown";
  return `${status.charAt(0).toUpperCase()}${status.slice(1)}`;
};

export default function Home() {
  const sermonsQuery = useQuery({
    queryKey: ["sermons"],
    queryFn: listSermons,
    refetchInterval: (query) => {
      const sermons = query.state.data || [];
      if (sermons.length === 0) {
        return false;
      }
      const shouldPoll = sermons.some((sermon) => {
        const progress = typeof sermon.progress === "number" ? sermon.progress : null;
        return (
          ACTIVE_STATUSES.has(sermon.status) || (progress !== null && progress < 100)
        );
      });
      return shouldPoll ? POLL_INTERVAL_MS : false;
    }
  });

  const sermons = sermonsQuery.data || [];
  const error = sermonsQuery.error?.message || "";
  const loading = sermonsQuery.isLoading;

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-8 px-6 py-16">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-[0.3em] text-slate-400">
          SermonClip Studio
        </p>
        <h1 className="text-4xl font-semibold">Sermon clip workspace</h1>
        <p className="text-slate-300">
          Upload sermons, track processing, and build clips in one place.
        </p>
      </header>

      <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <div>
          <p className="text-lg font-medium text-slate-100">Uploads</p>
          <p className="text-sm text-slate-400">
            Each upload starts a transcription job.
          </p>
        </div>
        <UploadSermon />
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-950/50">
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <p className="text-sm font-semibold text-slate-200">Recent sermons</p>
          {loading ? (
            <span className="inline-flex items-center gap-2 text-xs text-slate-500">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-700 border-t-emerald-400" />
              Loading sermons...
            </span>
          ) : null}
        </div>
        <div className="divide-y divide-slate-900">
          {loading
            ? Array.from({ length: LOADING_ROWS }).map((_, index) => (
                <div key={`loading-${index}`} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-2">
                      <div className="h-3 w-40 animate-pulse rounded bg-slate-900" />
                      <div className="h-2 w-32 animate-pulse rounded bg-slate-900/80" />
                    </div>
                    <div className="h-2 w-10 animate-pulse rounded bg-slate-900" />
                  </div>
                </div>
              ))
            : null}
          {error ? (
            <p className="px-6 py-4 text-sm text-red-400">{error}</p>
          ) : null}
          {!loading && sermons.length === 0 ? (
            <p className="px-6 py-4 text-sm text-slate-500">No sermons yet.</p>
          ) : null}
          {!loading ? sermons.map((sermon) => (
            <Link
              key={sermon.id}
              href={`/app/sermons/${sermon.id}`}
              className="block px-6 py-4 transition hover:bg-slate-900/60"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-medium text-slate-100">
                      {sermon.title || `Sermon #${sermon.id}`}
                    </p>
                    <span className="rounded-full border border-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
                      {formatStatus(sermon.status)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">
                    {typeof sermon.progress === "number"
                      ? `Progress ${Math.min(100, Math.max(0, sermon.progress))}%`
                      : "No progress yet"}
                  </p>
                  {sermon.error_message ? (
                    <p className="mt-1 text-xs text-red-400">
                      {sermon.error_message}
                    </p>
                  ) : null}
                  {typeof sermon.progress === "number" ? (
                    <div className="mt-2 h-1 w-40 rounded-full bg-slate-900">
                      <div
                        className="h-1 rounded-full bg-emerald-500/70"
                        style={{
                          width: `${Math.min(100, Math.max(0, sermon.progress))}%`
                        }}
                      />
                    </div>
                  ) : null}
                </div>
                <span className="text-xs text-slate-500">View</span>
              </div>
            </Link>
            )) : null}
        </div>
      </section>
    </main>
  );
}
