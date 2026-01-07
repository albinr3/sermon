"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import {
  acceptSuggestion,
  applyTrimSuggestion,
  createClip,
  generateEmbeddings,
  getSermon,
  getTranscriptSegments,
  getClip,
  listClips,
  listSuggestions,
  recordClipFeedback,
  renderClip,
  searchSermon,
  suggestClips
} from "../../../lib/api";

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

function formatTimestamp(ms) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function formatClipStatus(status) {
  if (!status) return "PENDING";
  if (status === "pending") return "PENDING";
  if (status === "processing") return "RUNNING";
  if (status === "done") return "DONE";
  if (status === "error") return "ERROR";
  return String(status).toUpperCase();
}

function formatTrimSuggestion(trim) {
  if (!trim || typeof trim !== "object") return "";
  const start = Number(trim.start_offset_sec || 0);
  const end = Number(trim.end_offset_sec || 0);
  const parts = [];
  if (Number.isFinite(start) && start > 0) {
    parts.push(`${Math.round(start)}s del inicio`);
  }
  if (Number.isFinite(end) && end !== 0) {
    parts.push(`${Math.round(Math.abs(end))}s del final`);
  }
  if (!parts.length) return "";
  return `IA sugiere recortar ${parts.join(" y ")}`;
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const pollClipUntilReady = async (clipId, timeoutMs = 180_000) => {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const clip = await getClip(clipId);
    if (clip?.status === "done" && (clip.download_url || clip.output_url)) {
      return clip;
    }
    await wait(POLL_INTERVAL_MS);
  }
  return null;
};

const triggerDownload = (url) => {
  if (!url) return;
  const link = document.createElement("a");
  link.href = url;
  link.rel = "noreferrer";
  link.download = "";
  document.body.appendChild(link);
  link.click();
  link.remove();
};

function ClipBuilder({
  title,
  subtitle,
  segments,
  initialStartMs,
  initialEndMs,
  actionLabel,
  busyLabel,
  onSubmit,
  onCancel
}) {
  const [selection, setSelection] = useState({ startIndex: null, endIndex: null });
  const [clipError, setClipError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setSelection({ startIndex: null, endIndex: null });
    setClipError("");
    if (!segments.length) {
      return;
    }
    if (initialStartMs === null || initialEndMs === null) {
      return;
    }
    let startIndex = segments.findIndex(
      (segment) =>
        segment.start_ms <= initialStartMs && segment.end_ms >= initialStartMs
    );
    if (startIndex === -1) {
      startIndex = segments.findIndex((segment) => segment.start_ms >= initialStartMs);
    }
    if (startIndex === -1) {
      startIndex = 0;
    }

    let endIndex = -1;
    for (let i = segments.length - 1; i >= 0; i -= 1) {
      const segment = segments[i];
      if (segment.start_ms <= initialEndMs && segment.end_ms >= initialEndMs) {
        endIndex = i;
        break;
      }
    }
    if (endIndex === -1) {
      endIndex = segments.findIndex((segment) => segment.end_ms >= initialEndMs);
    }
    if (endIndex === -1) {
      endIndex = segments.length - 1;
    }
    setSelection({ startIndex, endIndex });
  }, [segments, initialStartMs, initialEndMs]);

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

  const handleSubmit = async () => {
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

    setIsSubmitting(true);
    setClipError("");
    try {
      await onSubmit({
        start_ms: selectionStartMs,
        end_ms: selectionEndMs
      });
      setSelection({ startIndex: null, endIndex: null });
    } catch (err) {
      setClipError(isSafeError(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-950/50">
      <div className="border-b border-slate-800 px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-slate-200">{title}</p>
            {subtitle ? <p className="text-xs text-slate-500">{subtitle}</p> : null}
          </div>
          {onCancel ? (
            <button
              type="button"
              onClick={onCancel}
              className="rounded-full border border-slate-800 px-3 py-1 text-xs text-slate-300 hover:border-slate-700"
            >
              Cancel
            </button>
          ) : null}
        </div>
      </div>
      <div className="space-y-3 px-6 py-4">
        {segments.length === 0 ? (
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
      <div className="border-t border-slate-800 px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="text-sm text-slate-400">
            {selectionReady ? (
              <span>
                Range: {selectionStartMs}ms - {selectionEndMs}ms (
                {Math.round(selectionDurationMs / 1000)}s)
              </span>
            ) : (
              <span>No range selected.</span>
            )}
          </div>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="rounded-full border border-slate-800 px-4 py-2 text-sm text-slate-100 hover:border-slate-700 disabled:opacity-50"
          >
            {isSubmitting ? busyLabel : actionLabel}
          </button>
        </div>
        {clipError ? <p className="mt-2 text-sm text-red-400">{clipError}</p> : null}
      </div>
    </section>
  );
}

export default function SermonDetail({ params }) {
  const sermonId = params.id;
  const [sermon, setSermon] = useState(null);
  const [segments, setSegments] = useState([]);
  const [clips, setClips] = useState([]);
  const [clipsLoading, setClipsLoading] = useState(true);
  const hasLoadedClips = useRef(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [suggestions, setSuggestions] = useState([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(true);
  const [suggestionsError, setSuggestionsError] = useState("");
  const [suggesting, setSuggesting] = useState(false);
  const [suggestionsPending, setSuggestionsPending] = useState(false);
  const [useLlmSuggestions, setUseLlmSuggestions] = useState(
    process.env.NEXT_PUBLIC_DEFAULT_USE_LLM_FOR_CLIPS === "true"
  );
  const [actionLoading, setActionLoading] = useState({});
  const [editingSuggestion, setEditingSuggestion] = useState(null);
  const [suggestionClipMap, setSuggestionClipMap] = useState({});
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [embeddingLoading, setEmbeddingLoading] = useState(false);
  const [embeddingError, setEmbeddingError] = useState("");
  const [embeddingRequested, setEmbeddingRequested] = useState(false);
  const [jumpTarget, setJumpTarget] = useState(null);
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
    setSuggestionClipMap({});
  }, [sermonId]);

  useEffect(() => {
    setSuggestionsPending(false);
    setEmbeddingRequested(false);
    setEmbeddingLoading(false);
    setEmbeddingError("");
  }, [sermonId]);

  useEffect(() => {
    if (!sermon || !ACTIVE_STATUSES.has(sermon.status)) {
      return undefined;
    }

    const interval = setInterval(fetchSermon, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [sermon]);

  useEffect(() => {
    if (!embeddingRequested || sermon?.status === "embedded") {
      return undefined;
    }
    const interval = setInterval(fetchSermon, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [embeddingRequested, sermon?.status]);

  useEffect(() => {
    if (
      !sermon ||
      !["transcribed", "suggested", "completed", "embedded"].includes(sermon.status)
    ) {
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
      const filtered = data.filter(
        (clip) =>
          String(clip.sermon_id) === String(sermonId) &&
          String(clip.source) !== "auto"
      );
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

  const loadSuggestions = async () => {
    try {
      if (!suggestions.length) {
        setSuggestionsLoading(true);
      }
      const data = await listSuggestions(sermonId);
      setSuggestions(data.clips || []);
      setSuggestionsError("");
      if ((data.clips || []).length > 0) {
        setSuggestionsPending(false);
      }
    } catch (err) {
      setSuggestionsError(isSafeError(err));
      setSuggestionsPending(false);
    } finally {
      setSuggestionsLoading(false);
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

  useEffect(() => {
    loadSuggestions();
  }, [sermonId]);

  useEffect(() => {
    const shouldPoll =
      suggestions.length === 0 ||
      suggestions.some((clip) => CLIP_ACTIVE_STATUSES.has(clip.status));
    if (!shouldPoll) {
      return undefined;
    }
    const interval = setInterval(loadSuggestions, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [sermonId, suggestions]);

  const handleCreateClip = async ({ start_ms, end_ms, render_type }) => {
    const clip = await createClip({
      sermon_id: Number(sermonId),
      start_ms,
      end_ms,
      render_type
    });
    await renderClip(clip.id, render_type || "final");
    await loadClips();
    return clip;
  };

  const handleSuggest = async () => {
    setSuggesting(true);
    setSuggestionsError("");
    setSuggestionsPending(true);
    setSuggestions([]);
    setSuggestionsLoading(true);
    try {
      await suggestClips(sermonId, useLlmSuggestions);
      await loadSuggestions();
    } catch (err) {
      setSuggestionsError(isSafeError(err));
      setSuggestionsPending(false);
    } finally {
      setSuggesting(false);
    }
  };

  const setClipActionLoading = (clipId, value) => {
    setActionLoading((prev) => ({ ...prev, [clipId]: value }));
  };

  const getOrCreateManualClipId = async (suggestion) => {
    const existing = suggestionClipMap[suggestion.id];
    if (existing) {
      return existing;
    }
    const response = await acceptSuggestion(suggestion.id);
    const manualClipId = response.clip.id;
    setSuggestionClipMap((prev) => ({ ...prev, [suggestion.id]: manualClipId }));
    return manualClipId;
  };

  const handleAccept = async (suggestion) => {
    setClipActionLoading(suggestion.id, true);
    try {
      const manualClipId = await getOrCreateManualClipId(suggestion);
      await renderClip(manualClipId, "preview");
      await loadClips();
    } catch (err) {
      setError(isSafeError(err));
    } finally {
      setClipActionLoading(suggestion.id, false);
    }
  };

  const handleRender = async (suggestion, renderType) => {
    setClipActionLoading(suggestion.id, true);
    try {
      const manualClipId = await getOrCreateManualClipId(suggestion);
      await renderClip(manualClipId, renderType);
      await loadClips();
      if (renderType === "preview") {
        const clip = await pollClipUntilReady(manualClipId);
        if (clip) {
          triggerDownload(clip.download_url || clip.output_url);
        }
      }
    } catch (err) {
      setError(isSafeError(err));
    } finally {
      setClipActionLoading(suggestion.id, false);
    }
  };

  const handleApplyTrim = async (suggestion) => {
    setClipActionLoading(suggestion.id, true);
    try {
      const updated = await applyTrimSuggestion(suggestion.id);
      setSuggestions((prev) =>
        prev.map((clip) => (clip.id === updated.id ? updated : clip))
      );
    } catch (err) {
      setError(isSafeError(err));
    } finally {
      setClipActionLoading(suggestion.id, false);
    }
  };

  const handleReject = async (suggestion) => {
    setClipActionLoading(suggestion.id, true);
    try {
      await recordClipFeedback(suggestion.id, { accepted: false });
      setSuggestions((prev) =>
        prev.filter((clip) => String(clip.id) !== String(suggestion.id))
      );
    } catch (err) {
      setError(isSafeError(err));
    } finally {
      setClipActionLoading(suggestion.id, false);
    }
  };

  const requestEmbeddings = async () => {
    if (embeddingLoading || sermon?.status === "embedded") {
      return;
    }
    setEmbeddingLoading(true);
    setEmbeddingError("");
    try {
      await generateEmbeddings(sermonId);
      setEmbeddingRequested(true);
    } catch (err) {
      setEmbeddingError(isSafeError(err));
    } finally {
      setEmbeddingLoading(false);
    }
  };

  useEffect(() => {
    const query = searchQuery.trim();
    if (!query) {
      setSearchResults([]);
      setSearchError("");
      setSearchLoading(false);
      return;
    }
    if (!sermon) {
      return;
    }
    if (sermon.status !== "embedded") {
      setSearchResults([]);
      setSearchError("");
      setSearchLoading(false);
      if (!embeddingRequested) {
        requestEmbeddings();
      }
      return;
    }
    setSearchLoading(true);
    const timeout = setTimeout(async () => {
      try {
        const data = await searchSermon(sermonId, query, 10);
        setSearchResults(data.results || []);
        setSearchError("");
      } catch (err) {
        setSearchError(isSafeError(err));
      } finally {
        setSearchLoading(false);
      }
    }, 300);
    return () => clearTimeout(timeout);
  }, [searchQuery, sermonId, sermon, embeddingRequested]);

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

      <section className="rounded-2xl border border-slate-800 bg-slate-950/50 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-slate-200">Semantic Search</p>
            <p className="text-xs text-slate-500">
              Find moments by meaning, not exact words.
            </p>
          </div>
          {sermon?.status !== "embedded" ? (
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={requestEmbeddings}
                disabled={embeddingLoading}
                className="rounded-full border border-slate-800 px-4 py-2 text-xs text-slate-100 hover:border-slate-700 disabled:opacity-50"
              >
                {embeddingLoading ? "Generating..." : "Generate embeddings"}
              </button>
              {embeddingRequested ? (
                <span className="text-xs text-slate-500">
                  Embeddings are running…
                </span>
              ) : null}
            </div>
          ) : null}
        </div>
        <div className="mt-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search the sermon..."
            className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-600 focus:border-emerald-500/60 focus:outline-none"
          />
        </div>
        <div className="mt-4 space-y-3">
          {embeddingError ? (
            <p className="text-sm text-red-400">{embeddingError}</p>
          ) : sermon?.status !== "embedded" ? (
            <p className="text-sm text-slate-500">
              Embeddings are required for semantic search.{" "}
              {embeddingRequested ? "Generating them now..." : "Click to generate."}
            </p>
          ) : searchLoading ? (
            <div className="space-y-2">
              <div className="h-4 w-2/3 animate-pulse rounded bg-slate-900" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-slate-900" />
            </div>
          ) : searchError ? (
            <p className="text-sm text-red-400">{searchError}</p>
          ) : searchQuery.trim().length === 0 ? (
            <p className="text-sm text-slate-500">Type to search.</p>
          ) : searchResults.length === 0 ? (
            <p className="text-sm text-slate-500">No matches yet.</p>
          ) : (
            searchResults.map((result) => (
              <div
                key={result.segment_id}
                className="rounded-xl border border-slate-800 bg-slate-950/60 p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs text-slate-500">
                      {formatTimestamp(result.start_ms)} -{" "}
                      {formatTimestamp(result.end_ms)}
                    </p>
                    <p className="mt-1 text-sm text-slate-200">{result.text}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      setJumpTarget({
                        start_ms: result.start_ms,
                        end_ms: result.end_ms
                      })
                    }
                    className="rounded-full border border-slate-800 px-3 py-1 text-xs text-slate-100 hover:border-slate-700"
                  >
                    Jump
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      <ClipBuilder
        title="Transcript"
        subtitle="Select a start segment and an end segment."
        segments={segments}
        initialStartMs={jumpTarget?.start_ms ?? null}
        initialEndMs={jumpTarget?.end_ms ?? null}
        actionLabel="Create clip"
        busyLabel="Creating..."
        onSubmit={({ start_ms, end_ms }) =>
          handleCreateClip({ start_ms, end_ms, render_type: "final" })
        }
      />

      <section className="rounded-2xl border border-slate-800 bg-slate-950/50">
        <div className="border-b border-slate-800 px-6 py-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-slate-200">Suggested Clips</p>
              <p className="text-xs text-slate-500">Auto-selected ranges.</p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <label className="flex items-center gap-2 text-xs text-slate-400">
                <input
                  type="checkbox"
                  checked={useLlmSuggestions}
                  onChange={(event) => setUseLlmSuggestions(event.target.checked)}
                  disabled={suggesting}
                  className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-emerald-400"
                />
                Usar IA para sugerir clips
              </label>
              <button
                type="button"
                onClick={handleSuggest}
                disabled={suggesting}
                className="rounded-full border border-slate-800 px-4 py-2 text-sm text-slate-100 hover:border-slate-700 disabled:opacity-50"
              >
                {suggesting ? "Suggesting..." : "Generate suggestions"}
              </button>
              {suggesting ? (
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-700 border-t-emerald-500" />
                  Generando sugerencias...
                </div>
              ) : null}
            </div>
          </div>
        </div>
        <div className="divide-y divide-slate-900 px-6 py-4">
          {suggestionsLoading ? (
            <div className="space-y-3">
              <div className="h-6 w-48 animate-pulse rounded bg-slate-900" />
              <div className="h-6 w-40 animate-pulse rounded bg-slate-900" />
            </div>
          ) : suggestionsError ? (
            <p className="text-sm text-red-400">{suggestionsError}</p>
          ) : suggestionsPending ? (
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-700 border-t-emerald-500" />
              Generando sugerencias...
            </div>
          ) : suggestions.length === 0 ? (
            <p className="text-sm text-slate-500">No suggestions yet.</p>
          ) : (
            suggestions.map((clip) => {
              const isBusy = Boolean(actionLoading[clip.id]);
              const trimLabel = formatTrimSuggestion(clip.llm_trim);
              return (
                <div key={clip.id} className="flex flex-col gap-3 py-4">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="text-sm text-slate-200">
                        {formatTimestamp(clip.start_ms)} - {formatTimestamp(clip.end_ms)}
                      </p>
                      <p className="text-xs text-slate-500">
                        Score {clip.score?.toFixed(2) ?? "0.00"} -{" "}
                        {formatClipStatus(clip.status)}
                        {clip.use_llm ? (
                          <span className="ml-2 inline-flex rounded-full border border-emerald-500/40 px-2 py-0.5 text-[10px] uppercase tracking-wide text-emerald-300">
                            IA
                          </span>
                        ) : null}
                      </p>
                      {clip.rationale ? (
                        <p className="mt-2 text-xs text-slate-400">
                          {clip.rationale}
                        </p>
                      ) : null}
                      {trimLabel ? (
                        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                          <span>{trimLabel}</span>
                          {clip.trim_applied ? (
                            <span className="rounded-full border border-emerald-500/40 px-2 py-0.5 text-[10px] uppercase tracking-wide text-emerald-300">
                              Recorte aplicado
                            </span>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleApplyTrim(clip)}
                              disabled={isBusy}
                              className="rounded-full border border-emerald-500/50 px-2 py-0.5 text-[10px] uppercase tracking-wide text-emerald-200 hover:border-emerald-400 disabled:opacity-50"
                            >
                              Aplicar
                            </button>
                          )}
                        </div>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => handleRender(clip, "preview")}
                        disabled={isBusy}
                        className="rounded-full border border-slate-800 px-3 py-1 text-xs text-slate-100 hover:border-slate-700 disabled:opacity-50"
                      >
                        Preview
                      </button>
                      <button
                        type="button"
                        onClick={() => handleRender(clip, "final")}
                        disabled={isBusy}
                        className="rounded-full border border-slate-800 px-3 py-1 text-xs text-slate-100 hover:border-slate-700 disabled:opacity-50"
                      >
                        Render Final
                      </button>
                      <button
                        type="button"
                        onClick={() => handleAccept(clip)}
                        disabled={isBusy}
                        className="rounded-full border border-emerald-500/50 px-3 py-1 text-xs text-emerald-200 hover:border-emerald-400 disabled:opacity-50"
                      >
                        Accept
                      </button>
                      <button
                        type="button"
                        onClick={() => handleReject(clip)}
                        disabled={isBusy}
                        className="rounded-full border border-rose-500/50 px-3 py-1 text-xs text-rose-200 hover:border-rose-400 disabled:opacity-50"
                      >
                        Reject
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingSuggestion(clip)}
                        className="rounded-full border border-slate-800 px-3 py-1 text-xs text-slate-100 hover:border-slate-700"
                      >
                        Edit Range
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </section>

      {editingSuggestion ? (
        <ClipBuilder
          title="Edit Suggested Clip"
          subtitle="Adjust the range and save as a manual clip."
          segments={segments}
          initialStartMs={editingSuggestion.start_ms}
          initialEndMs={editingSuggestion.end_ms}
          actionLabel="Save clip"
          busyLabel="Saving..."
          onSubmit={async ({ start_ms, end_ms }) => {
            await handleCreateClip({ start_ms, end_ms, render_type: "final" });
            setEditingSuggestion(null);
          }}
          onCancel={() => setEditingSuggestion(null)}
        />
      ) : null}

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
                  <p className="text-xs text-slate-500">
                    {formatClipStatus(clip.status)}
                  </p>
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
                    {formatClipStatus(clip.status)}
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
