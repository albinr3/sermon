"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";

import {
  acceptSuggestion,
  applyTrimSuggestion,
  createClip,
  generateEmbeddings,
  getClip,
  getSermon,
  getTranscriptSegments,
  listClips,
  listSuggestions,
  recordClipFeedback,
  renderClip,
  searchSermon,
  suggestClips
} from "../../../lib/api";

const ClipBuilder = dynamic(() => import("./components/ClipBuilder"), {
  loading: () => (
    <section className="rounded-2xl border border-slate-800 bg-slate-950/50">
      <div className="h-48 animate-pulse rounded-2xl bg-slate-900/60" />
    </section>
  )
});

const SuggestedClipsPanel = dynamic(
  () => import("./components/SuggestedClipsPanel"),
  {
    loading: () => (
      <section className="rounded-2xl border border-slate-800 bg-slate-950/50 p-6">
        <div className="h-6 w-48 animate-pulse rounded bg-slate-900" />
      </section>
    )
  }
);

const POLL_INTERVAL_MS = 3000;
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

export default function SermonDetail({ params }) {
  const sermonId = params.id;
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [suggestionsPending, setSuggestionsPending] = useState(false);
  const [suggestionsError, setSuggestionsError] = useState("");
  const [useLlmSuggestions, setUseLlmSuggestions] = useState(
    process.env.NEXT_PUBLIC_DEFAULT_USE_LLM_FOR_CLIPS === "true"
  );
  const [actionLoading, setActionLoading] = useState({});
  const [editingSuggestion, setEditingSuggestion] = useState(null);
  const [suggestionClipMap, setSuggestionClipMap] = useState({});
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [embeddingError, setEmbeddingError] = useState("");
  const [embeddingRequested, setEmbeddingRequested] = useState(false);
  const [jumpTarget, setJumpTarget] = useState(null);

  useEffect(() => {
    setSuggestionClipMap({});
    setSuggestionsPending(false);
    setSuggestionsError("");
    setEmbeddingRequested(false);
    setEmbeddingError("");
    setEditingSuggestion(null);
    setJumpTarget(null);
    setError("");
  }, [sermonId]);

  useEffect(() => {
    const query = searchQuery.trim();
    if (!query) {
      setDebouncedQuery("");
      return;
    }
    const timeout = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(timeout);
  }, [searchQuery]);

  const sermonQuery = useQuery({
    queryKey: ["sermon", sermonId],
    queryFn: () => getSermon(sermonId),
    refetchInterval: (query) => {
      const sermon = query.state.data;
      if (!sermon) {
        return false;
      }
      if (ACTIVE_STATUSES.has(sermon.status)) {
        return POLL_INTERVAL_MS;
      }
      if (embeddingRequested && sermon.status !== "embedded") {
        return POLL_INTERVAL_MS;
      }
      return false;
    }
  });

  const sermon = sermonQuery.data ?? null;
  const loading = sermonQuery.isLoading;
  const statusError = error || sermonQuery.error?.message || "";
  const progress =
    typeof sermon?.progress === "number"
      ? Math.min(100, Math.max(0, sermon.progress))
      : null;

  const segmentsQuery = useQuery({
    queryKey: ["segments", sermonId],
    queryFn: () => getTranscriptSegments(sermonId),
    enabled:
      Boolean(sermon) &&
      ["transcribed", "suggested", "completed", "embedded"].includes(
        sermon.status
      )
  });
  const segments = segmentsQuery.data || [];

  const clipsQuery = useQuery({
    queryKey: ["clips", sermonId],
    queryFn: async () => {
      const data = await listClips();
      return data.filter(
        (clip) =>
          String(clip.sermon_id) === String(sermonId) &&
          String(clip.source) !== "auto"
      );
    },
    refetchInterval: (query) => {
      const clips = query.state.data || [];
      if (clips.length === 0) {
        return POLL_INTERVAL_MS;
      }
      const shouldPoll = clips.some((clip) =>
        CLIP_ACTIVE_STATUSES.has(clip.status)
      );
      return shouldPoll ? POLL_INTERVAL_MS : false;
    }
  });
  const clips = clipsQuery.data || [];
  const clipsLoading = clipsQuery.isLoading;

  const suggestionsQuery = useQuery({
    queryKey: ["suggestions", sermonId],
    queryFn: () => listSuggestions(sermonId),
    refetchInterval: (query) => {
      const clips = query.state.data?.clips || [];
      if (clips.length === 0) {
        return POLL_INTERVAL_MS;
      }
      const shouldPoll = clips.some((clip) =>
        CLIP_ACTIVE_STATUSES.has(clip.status)
      );
      return shouldPoll ? POLL_INTERVAL_MS : false;
    }
  });
  const suggestions = suggestionsQuery.data?.clips || [];
  const suggestionsLoading = suggestionsQuery.isLoading;
  const suggestionsErrorMessage =
    suggestionsError || suggestionsQuery.error?.message || "";

  useEffect(() => {
    if (suggestions.length > 0) {
      setSuggestionsPending(false);
    }
  }, [suggestions.length]);

  useEffect(() => {
    if (suggestionsQuery.isError) {
      setSuggestionsPending(false);
    }
  }, [suggestionsQuery.isError]);

  const embeddingMutation = useMutation({
    mutationFn: () => generateEmbeddings(sermonId),
    onSuccess: () => {
      setEmbeddingRequested(true);
    },
    onError: (err) => {
      setEmbeddingError(isSafeError(err));
    }
  });
  const embeddingLoading = embeddingMutation.isPending;

  const requestEmbeddings = async () => {
    if (embeddingLoading || sermon?.status === "embedded") {
      return;
    }
    setEmbeddingError("");
    try {
      await embeddingMutation.mutateAsync();
    } catch (err) {
      setEmbeddingError(isSafeError(err));
    }
  };

  const searchQueryResult = useQuery({
    queryKey: ["search", sermonId, debouncedQuery],
    queryFn: () => searchSermon(sermonId, debouncedQuery, 10),
    enabled: Boolean(debouncedQuery) && sermon?.status === "embedded"
  });
  const hasSearchInput = searchQuery.trim().length > 0;
  const searchResults = searchQueryResult.data?.results || [];
  const searchLoading =
    hasSearchInput && (debouncedQuery ? searchQueryResult.isFetching : true);
  const searchError =
    hasSearchInput && debouncedQuery
      ? searchQueryResult.error?.message || ""
      : "";

  const suggestMutation = useMutation({
    mutationFn: () => suggestClips(sermonId, useLlmSuggestions),
    onMutate: () => {
      setSuggestionsPending(true);
      setSuggestionsError("");
      queryClient.setQueryData(["suggestions", sermonId], {
        sermon_id: Number(sermonId),
        clips: []
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions", sermonId] });
    },
    onError: (err) => {
      setSuggestionsError(isSafeError(err));
      setSuggestionsPending(false);
    }
  });
  const suggesting = suggestMutation.isPending;

  useEffect(() => {
    const query = searchQuery.trim();
    if (!query || !sermon || sermon.status === "embedded") {
      return;
    }
    if (!embeddingRequested && !embeddingLoading) {
      requestEmbeddings();
    }
  }, [searchQuery, sermon, embeddingRequested, embeddingLoading]);

  const handleCreateClip = async ({ start_ms, end_ms, render_type }) => {
    const clip = await createClip({
      sermon_id: Number(sermonId),
      start_ms,
      end_ms,
      render_type
    });
    await renderClip(clip.id, render_type || "final");
    await queryClient.invalidateQueries({ queryKey: ["clips", sermonId] });
    return clip;
  };

  const handleSuggest = () => {
    suggestMutation.mutate();
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
    await queryClient.invalidateQueries({ queryKey: ["clips", sermonId] });
    return manualClipId;
  };

  const handleAccept = async (suggestion) => {
    setClipActionLoading(suggestion.id, true);
    try {
      const manualClipId = await getOrCreateManualClipId(suggestion);
      await renderClip(manualClipId, "preview");
      await queryClient.invalidateQueries({ queryKey: ["clips", sermonId] });
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
      await queryClient.invalidateQueries({ queryKey: ["clips", sermonId] });
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
      queryClient.setQueryData(["suggestions", sermonId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          clips: prev.clips.map((clip) =>
            clip.id === updated.id ? updated : clip
          )
        };
      });
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
      queryClient.setQueryData(["suggestions", sermonId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          clips: prev.clips.filter(
            (clip) => String(clip.id) !== String(suggestion.id)
          )
        };
      });
    } catch (err) {
      setError(isSafeError(err));
    } finally {
      setClipActionLoading(suggestion.id, false);
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
        ) : statusError ? (
          <p className="mt-2 text-sm text-red-400">{statusError}</p>
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
                  Embeddings are running.
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
          ) : !hasSearchInput ? (
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

      <SuggestedClipsPanel
        useLlmSuggestions={useLlmSuggestions}
        onToggleUseLlm={setUseLlmSuggestions}
        onSuggest={handleSuggest}
        suggesting={suggesting}
        suggestionsLoading={suggestionsLoading}
        suggestionsError={suggestionsErrorMessage}
        suggestionsPending={suggestionsPending}
        suggestions={suggestions}
        actionLoading={actionLoading}
        onApplyTrim={handleApplyTrim}
        onRender={handleRender}
        onAccept={handleAccept}
        onReject={handleReject}
        onEdit={setEditingSuggestion}
        formatTimestamp={formatTimestamp}
        formatClipStatus={formatClipStatus}
        formatTrimSuggestion={formatTrimSuggestion}
      />

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
