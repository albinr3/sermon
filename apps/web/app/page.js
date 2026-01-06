"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import UploadSermon from "./components/UploadSermon";
import { listSermons } from "../lib/api";

const POLL_INTERVAL_MS = 3000;
const ACTIVE_STATUSES = new Set(["pending", "uploaded", "processing"]);

export default function Home() {
  const [sermons, setSermons] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadSermons = async () => {
    try {
      setLoading(true);
      const data = await listSermons();
      setSermons(data);
      setError("");
    } catch (err) {
      setError(err.message || "Failed to load sermons");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSermons();
  }, []);

  useEffect(() => {
    if (sermons.length === 0) {
      return undefined;
    }
    const shouldPoll = sermons.some((sermon) => {
      const progress = typeof sermon.progress === "number" ? sermon.progress : null;
      return ACTIVE_STATUSES.has(sermon.status) || (progress !== null && progress < 100);
    });
    if (!shouldPoll) {
      return undefined;
    }
    const interval = setInterval(loadSermons, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [sermons]);

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-8 px-6 py-16">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Sermon MVP</p>
        <h1 className="text-4xl font-semibold">Sermon dashboard</h1>
        <p className="text-slate-300">
          Upload a sermon, transcribe it, and monitor progress.
        </p>
      </header>

      <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <div>
          <p className="text-lg font-medium text-slate-100">Uploads</p>
          <p className="text-sm text-slate-400">
            Each upload starts a transcription job.
          </p>
        </div>
        <UploadSermon onUploaded={loadSermons} />
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-950/50">
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <p className="text-sm font-semibold text-slate-200">Recent sermons</p>
          {loading ? <span className="text-xs text-slate-500">Loading...</span> : null}
        </div>
        <div className="divide-y divide-slate-900">
          {error ? (
            <p className="px-6 py-4 text-sm text-red-400">{error}</p>
          ) : null}
          {!loading && sermons.length === 0 ? (
            <p className="px-6 py-4 text-sm text-slate-500">No sermons yet.</p>
          ) : null}
          {sermons.map((sermon) => (
            <Link
              key={sermon.id}
              href={`/sermons/${sermon.id}`}
              className="block px-6 py-4 transition hover:bg-slate-900/60"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-100">
                    {sermon.title || `Sermon #${sermon.id}`}
                  </p>
                  <p className="text-xs text-slate-500">
                    {sermon.status}
                    {typeof sermon.progress === "number"
                      ? ` · ${Math.min(100, Math.max(0, sermon.progress))}%`
                      : ""}
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
          ))}
        </div>
      </section>
    </main>
  );
}
