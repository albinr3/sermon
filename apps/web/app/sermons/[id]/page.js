"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { createClip, getSermon, getTranscriptSegments, listClips } from "../../../lib/api";

const POLL_INTERVAL_MS = 3000;
const MIN_DURATION_MS = 10_000;
const MAX_DURATION_MS = 120_000;
const ACTIVE_STATUSES = new Set(["pending", "processing", "uploaded"]);
const CLIP_ACTIVE_STATUSES = new Set(["pending", "processing"]);

function isSafeError(err) {
  if (!err) return "Unknown error";
  const message = err.message || String(err);
  return message.slice(0, 200);
}

export default function SermonDetail({ params }) {
  const sermonId = params.id;
  const [sermon, setSermon] = useState(null);
  const [segments, setSegments] = useState([]);
  const [clips, setClips] = useState([]);
  const [clipsLoading, setClipsLoading] = useState(true);
  const hasLoadedClips = useRef(false);
  const [selection, setSelection] = useState({ startIndex: null, endIndex: null });
  const [clipError, setClipError] = useState("");
  const [clipLoading, setClipLoading] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const progress =
    typeof sermon?.progress === "number"
      ? Math.min(100, Math.max(0, sermon.progress))
      : null;

  const fetchSermon = async () => {
    try {
      const data = await getSermon(sermonId);
      setSermon(data);
      setError("");
    } catch (err) {
      setError(isSafeError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSermon();
  }, [sermonId]);

  useEffect(() => {
    if (!sermon || !ACTIVE_STATUSES.has(sermon.status)) {
      return undefined;
    }

    const interval = setInterval(fetchSermon, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [sermon]);

  useEffect(() => {
    if (!sermon || sermon.status !== "transcribed") {
      return;
    }

    const loadSegments = async () => {
      try {
        const data = await getTranscriptSegments(sermonId);
        setSegments(data);
      } catch (err) {
        setError(isSafeError(err));
      }
    };

    loadSegments();
  }, [sermon, sermonId]);

  const areClipsEqual = (prevClips, nextClips) => {
    if (prevClips.length !== nextClips.length) {
      return false;
    }
    for (let i = 0; i < prevClips.length; i += 1) {
      const prev = prevClips[i];
      const next = nextClips[i];
      if (!prev || !next) {
        return false;
      }
      if (
        prev.id !== next.id ||
        prev.status !== next.status ||
        prev.output_url !== next.output_url
      ) {
        return false;
      }
    }
    return true;
  };

  const loadClips = async () => {
    try {
      if (!hasLoadedClips.current) {
        setClipsLoading(true);
      }
      const data = await listClips();
      const filtered = data.filter((clip) => String(clip.sermon_id) === String(sermonId));
      setClips((prev) => (areClipsEqual(prev, filtered) ? prev : filtered));
    } catch (err) {
      setError(isSafeError(err));
    } finally {
      if (!hasLoadedClips.current) {
        hasLoadedClips.current = true;
        setClipsLoading(false);
      }
    }
  };

  useEffect(() => {
    hasLoadedClips.current = false;
    setClipsLoading(true);
    loadClips();
  }, [sermonId]);

  useEffect(() => {
    const shouldPoll =
      clips.length === 0 || clips.some((clip) => CLIP_ACTIVE_STATUSES.has(clip.status));
    if (!shouldPoll) {
      return undefined;
    }
    const interval = setInterval(loadClips, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [sermonId, clips]);

  const selectionReady =
    selection.startIndex !== null && selection.endIndex !== null && segments.length > 0;

  const selectionRange = selectionReady
    ? [
        Math.min(selection.startIndex, selection.endIndex),
        Math.max(selection.startIndex, selection.endIndex)
      ]
    : null;

  const selectionSegments = selectionRange
    ? segments.slice(selectionRange[0], selectionRange[1] + 1)
    : [];

  const selectionStartMs = selectionSegments.length
    ? selectionSegments[0].start_ms
    : null;
  const selectionEndMs = selectionSegments.length
    ? selectionSegments[selectionSegments.length - 1].end_ms
    : null;
  const selectionDurationMs =
    selectionStartMs !== null && selectionEndMs !== null
      ? selectionEndMs - selectionStartMs
      : 0;

  const handleSegmentClick = (index) => {
    setClipError("");
    if (selection.startIndex === null || selection.endIndex !== null) {
      setSelection({ startIndex: index, endIndex: null });
      return;
    }
    setSelection((prev) => ({ ...prev, endIndex: index }));
  };

  const handleCreateClip = async () => {
    if (!selectionReady || selectionStartMs === null || selectionEndMs === null) {
      setClipError("Select a start and end segment first.");
      return;
    }

    if (selectionDurationMs < MIN_DURATION_MS) {
      setClipError("Clip must be at least 10 seconds.");
      return;
    }

    if (selectionDurationMs > MAX_DURATION_MS) {
      setClipError("Clip must be at most 120 seconds.");
      return;
    }

    setClipLoading(true);
    setClipError("");
    try {
      await createClip({
        sermon_id: Number(sermonId),
        start_ms: selectionStartMs,
        end_ms: selectionEndMs
      });
      const updated = await listClips();
      setClips(updated.filter((clip) => String(clip.sermon_id) === String(sermonId)));
      setSelection({ startIndex: null, endIndex: null });
    } catch (err) {
      setClipError(isSafeError(err));
    } finally {
      setClipLoading(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-8 px-6 py-16">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Sermon</p>
          <h1 className="text-3xl font-semibold text-slate-100">
            {sermon?.title || `Sermon #${sermonId}`}
          </h1>
          <p className="text-sm text-slate-500">{sermon?.status || "loading"}</p>
        </div>
        <Link
          href="/"
          className="rounded-full border border-slate-800 px-4 py-2 text-sm text-slate-300 hover:border-slate-700"
        >
          Back
        </Link>
      </div>

      <section className="rounded-2xl border border-slate-800 bg-slate-950/50 p-6">
        <p className="text-sm text-slate-400">Status</p>
        {loading ? (
          <div className="mt-2 space-y-2">
            <div className="h-4 w-40 animate-pulse rounded bg-slate-800" />
            <div className="h-3 w-56 animate-pulse rounded bg-slate-900" />
          </div>
        ) : error ? (
          <p className="mt-2 text-sm text-red-400">{error}</p>
        ) : (
          <div className="mt-2 space-y-2">
            <p className="text-lg font-medium text-slate-100">{sermon?.status}</p>
            {progress !== null ? (
              <div className="space-y-1">
                <div className="h-2 w-full max-w-xs rounded-full bg-slate-900">
                  <div
                    className="h-2 rounded-full bg-emerald-500/70"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="text-xs text-slate-500">{progress}%</p>
              </div>
            ) : null}
            {sermon?.error_message ? (
              <p className="text-sm text-red-400">{sermon.error_message}</p>
            ) : null}
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-950/50">
        <div className="border-b border-slate-800 px-6 py-4">
          <p className="text-sm font-semibold text-slate-200">Transcript</p>
        </div>
        <div className="space-y-3 px-6 py-4">
          {sermon?.status !== "transcribed" ? (
            <div className="space-y-2">
              <p className="text-sm text-slate-500">
                Waiting for transcription to finish...
              </p>
              <div className="space-y-2">
                <div className="h-4 w-full animate-pulse rounded bg-slate-900" />
                <div className="h-4 w-5/6 animate-pulse rounded bg-slate-900" />
                <div className="h-4 w-4/6 animate-pulse rounded bg-slate-900" />
              </div>
            </div>
          ) : segments.length === 0 ? (
            <p className="text-sm text-slate-500">No segments available.</p>
          ) : (
            <div className="space-y-3">
              {segments.map((segment, index) => {
                const isSelected =
                  selectionRange &&
                  index >= selectionRange[0] &&
                  index <= selectionRange[1];
                return (
                  <button
                    key={segment.id}
                    type="button"
                    onClick={() => handleSegmentClick(index)}
                    className={`w-full rounded-lg border p-3 text-left transition ${
                      isSelected
                        ? "border-emerald-500/70 bg-emerald-500/10"
                        : "border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <p className="text-xs text-slate-500">
                      {segment.start_ms}ms - {segment.end_ms}ms
                    </p>
                    <p className="text-sm text-slate-200">{segment.text}</p>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-950/50 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-slate-200">Clip builder</p>
            <p className="text-xs text-slate-500">
              Select a start segment and an end segment.
            </p>
          </div>
          <button
            type="button"
            onClick={handleCreateClip}
            disabled={clipLoading}
            className="rounded-full border border-slate-800 px-4 py-2 text-sm text-slate-100 hover:border-slate-700 disabled:opacity-50"
          >
            {clipLoading ? "Creating..." : "Create clip"}
          </button>
        </div>
        <div className="mt-4 text-sm text-slate-400">
          {selectionReady ? (
            <span>
              Range: {selectionStartMs}ms - {selectionEndMs}ms (
              {Math.round(selectionDurationMs / 1000)}s)
            </span>
          ) : (
            <span>No range selected.</span>
          )}
        </div>
        {clipError ? <p className="mt-2 text-sm text-red-400">{clipError}</p> : null}
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-950/50">
        <div className="border-b border-slate-800 px-6 py-4">
          <p className="text-sm font-semibold text-slate-200">Clips</p>
        </div>
        <div className="divide-y divide-slate-900 px-6 py-4">
          {clipsLoading ? (
            <div className="space-y-3">
              <div className="h-6 w-48 animate-pulse rounded bg-slate-900" />
              <div className="h-6 w-40 animate-pulse rounded bg-slate-900" />
            </div>
          ) : clips.length === 0 ? (
            <p className="text-sm text-slate-500">No clips yet.</p>
          ) : (
            clips.map((clip) => (
              <div key={clip.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm text-slate-200">
                    {Math.round((clip.end_ms - clip.start_ms) / 1000)}s clip
                  </p>
                  <p className="text-xs text-slate-500">{clip.status}</p>
                </div>
                {clip.status === "done" ? (
                  <a
                    href={clip.download_url || clip.output_url || "#"}
                    className="text-sm text-emerald-400 hover:text-emerald-300"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Download
                  </a>
                ) : (
                  <span className="text-xs text-slate-500">
                    {clip.status === "error" ? "Error" : "Processing"}
                  </span>
                )}
              </div>
            ))
          )}
        </div>
      </section>
    </main>
  );
}
