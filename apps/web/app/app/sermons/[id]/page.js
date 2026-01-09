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
} from "../../../../lib/api";

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
const PREVIEW_WARMUP_COUNT = 1;
const SERMON_STATUS_ORDER = {
  pending: 0,
  uploaded: 1,
  processing: 2,
  transcribed: 3,
  suggested: 4,
  embedded: 5,
  completed: 6
};
const WORKFLOW_STATE_META = {
  done: {
    label: "Done",
    badge: "border-emerald-500/40 bg-emerald-500/10 text-emerald-200",
    dot: "bg-emerald-400"
  },
  active: {
    label: "In progress",
    badge: "border-amber-500/40 bg-amber-500/10 text-amber-200",
    dot: "bg-amber-400"
  },
  idle: {
    label: "Ready",
    badge: "border-slate-800 bg-slate-900/60 text-slate-300",
    dot: "bg-slate-500"
  },
  blocked: {
    label: "Waiting",
    badge: "border-slate-800 bg-slate-900/40 text-slate-500",
    dot: "bg-slate-600"
  },
  error: {
    label: "Error",
    badge: "border-rose-500/40 bg-rose-500/10 text-rose-200",
    dot: "bg-rose-400"
  }
};

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

const NOTICE_STYLES = {
  info: "border-slate-800 bg-slate-900/60 text-slate-200",
  success: "border-emerald-500/40 bg-emerald-500/10 text-emerald-200",
  error: "border-rose-500/40 bg-rose-500/10 text-rose-200"
};

const getWorkflowMeta = (state) => WORKFLOW_STATE_META[state] || WORKFLOW_STATE_META.idle;

const isPreviewReady = (clip) =>
  clip?.render_type === "preview" &&
  clip?.status === "done" &&
  Boolean(clip?.download_url || clip?.output_url);

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
  const [notice, setNotice] = useState(null);
  const [suggestionsProgress, setSuggestionsProgress] = useState(0);
  const [previewClip, setPreviewClip] = useState(null);
  const [isTranscriptOpen, setIsTranscriptOpen] = useState(false);

  const pushNotice = (message, tone = "info") => {
    setNotice({ message, tone });
  };

  useEffect(() => {
    setSuggestionClipMap({});
    setSuggestionsPending(false);
    setSuggestionsError("");
    setEmbeddingRequested(false);
    setEmbeddingError("");
    setEditingSuggestion(null);
    setJumpTarget(null);
    setError("");
    setNotice(null);
    setSuggestionsProgress(0);
    setPreviewClip(null);
    setIsTranscriptOpen(false);
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

  useEffect(() => {
    if (jumpTarget) {
      setIsTranscriptOpen(true);
    }
  }, [jumpTarget]);

  useEffect(() => {
    if (!notice) return;
    const timeout = setTimeout(() => setNotice(null), 4500);
    return () => clearTimeout(timeout);
  }, [notice]);

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
  const rawSourceUrl = sermon?.source_download_url || sermon?.source_url || null;
  const sermonSourceUrl =
    rawSourceUrl && /^https?:\/\//.test(rawSourceUrl) ? rawSourceUrl : null;

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
  const sortedSuggestions = [...suggestions].sort((a, b) => {
    const scoreDiff = (b.score ?? 0) - (a.score ?? 0);
    if (scoreDiff !== 0) return scoreDiff;
    return b.id - a.id;
  });
  const warmupTarget = Math.min(PREVIEW_WARMUP_COUNT, sortedSuggestions.length);
  const warmupCandidates = sortedSuggestions.slice(0, warmupTarget);
  const warmupReadyCount = warmupCandidates.filter(isPreviewReady).length;
  const warmupPending = warmupTarget > 0 && warmupReadyCount < warmupTarget;
  const suggestionsProgressLabel = suggestionsPending
    ? "Generating suggestions..."
    : warmupPending
    ? `Rendering preview (${warmupReadyCount}/${warmupTarget})`
    : "";
  const suggestionsLocked = suggestionsPending || warmupPending;

  useEffect(() => {
    if (!suggestionsPending) {
      return;
    }
    setSuggestionsProgress((prev) => (prev > 0 ? prev : 4));
    const interval = setInterval(() => {
      setSuggestionsProgress((prev) => {
        const bump = prev < 55 ? 1.5 + Math.random() * 1.5 : 0.5 + Math.random();
        return Math.min(prev + bump, 70);
      });
    }, 900);
    return () => clearInterval(interval);
  }, [suggestionsPending]);

  useEffect(() => {
    if (suggestionsPending || !warmupPending) {
      return;
    }
    setSuggestionsProgress((prev) => (prev < 70 ? 70 : prev));
    const interval = setInterval(() => {
      setSuggestionsProgress((prev) => {
        const bump = prev < 85 ? 0.8 + Math.random() * 0.8 : 0.3 + Math.random();
        return Math.min(prev + bump, 95);
      });
    }, 900);
    return () => clearInterval(interval);
  }, [suggestionsPending, warmupPending]);

  useEffect(() => {
    if (suggestionsPending || warmupPending) {
      return;
    }
    if (warmupTarget === 0) {
      setSuggestionsProgress(0);
      return;
    }
    const interval = setInterval(() => {
      setSuggestionsProgress((prev) => {
        if (prev >= 100) {
          return 100;
        }
        const bump = prev < 98 ? 0.8 + Math.random() * 0.6 : 0.2 + Math.random() * 0.2;
        return Math.min(100, prev + bump);
      });
    }, 220);
    const timeout = setTimeout(() => setSuggestionsProgress(0), 1200);
    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [suggestionsPending, warmupPending, warmupTarget]);

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
      pushNotice("Embeddings requested. Search will update when ready.", "success");
    },
    onError: (err) => {
      setEmbeddingError(isSafeError(err));
      pushNotice("Embedding request failed. Try again.", "error");
    }
  });
  const embeddingLoading = embeddingMutation.isPending;

  const sermonStatus = sermon?.status || null;
  const statusRank =
    sermonStatus && SERMON_STATUS_ORDER[sermonStatus] !== undefined
      ? SERMON_STATUS_ORDER[sermonStatus]
      : null;
  const hasErrorStatus = sermonStatus === "error" || sermonStatus === "failed";
  const clipActive = clips.some((clip) => CLIP_ACTIVE_STATUSES.has(clip.status));
  const clipDoneCount = clips.filter((clip) => clip.status === "done").length;

  const uploadState = (() => {
    if (!sermonStatus) return "idle";
    if (hasErrorStatus) return "error";
    if (sermonStatus === "pending") return "active";
    return "done";
  })();

  const transcriptionState = (() => {
    if (!sermonStatus) return "idle";
    if (hasErrorStatus) return "error";
    if (sermonStatus === "processing") return "active";
    if (statusRank !== null && statusRank >= SERMON_STATUS_ORDER.transcribed) {
      return "done";
    }
    if (sermonStatus === "uploaded") return "idle";
    return "blocked";
  })();

  const suggestionsState = (() => {
    if (!sermonStatus) return "idle";
    if (hasErrorStatus) return "error";
    if (suggestionsPending || suggestionsLoading) return "active";
    if (
      suggestions.length > 0 ||
      (statusRank !== null && statusRank >= SERMON_STATUS_ORDER.suggested)
    ) {
      return "done";
    }
    if (statusRank !== null && statusRank >= SERMON_STATUS_ORDER.transcribed) {
      return "idle";
    }
    return "blocked";
  })();

  const embeddingsState = (() => {
    if (!sermonStatus) return "idle";
    if (hasErrorStatus) return "error";
    if (sermonStatus === "embedded") return "done";
    if (embeddingRequested || embeddingLoading) return "active";
    if (statusRank !== null && statusRank >= SERMON_STATUS_ORDER.transcribed) {
      return "idle";
    }
    return "blocked";
  })();

  const rendersState = (() => {
    if (!sermonStatus) return "idle";
    if (hasErrorStatus) return "error";
    if (clipActive) return "active";
    if (clipDoneCount > 0) return "done";
    return "idle";
  })();

  const workflowCards = [
    {
      title: "Upload",
      state: uploadState,
      detail: sermonSourceUrl ? "Source video ready." : "Waiting for upload."
    },
    {
      title: "Transcription",
      state: transcriptionState,
      detail:
        progress !== null
          ? `Progress ${progress}%`
          : sermonStatus === "processing"
          ? "Transcribing..."
          : "Pending transcription."
    },
    {
      title: "Suggestions",
      state: suggestionsState,
      detail:
        suggestions.length > 0
          ? `${suggestions.length} suggestions ready.`
          : suggestionsPending
          ? "Generating suggestions..."
          : "No suggestions yet."
    },
    {
      title: "Embeddings",
      state: embeddingsState,
      detail:
        sermonStatus === "embedded"
          ? "Search enabled."
          : embeddingRequested
          ? "Embedding in progress..."
          : "Generate when needed."
    },
    {
      title: "Renders",
      state: rendersState,
      detail:
        clipActive
          ? "Rendering clips..."
          : clipDoneCount > 0
          ? `${clipDoneCount} clips ready.`
          : "No clips rendered."
    }
  ];

  const previewUrl = (() => {
    const candidate = previewClip?.download_url || previewClip?.output_url || "";
    if (!candidate) return "";
    return /^https?:\/\//.test(candidate) ? candidate : "";
  })();

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
      pushNotice("Suggestion generation started.", "success");
    },
    onError: (err) => {
      setSuggestionsError(isSafeError(err));
      setSuggestionsPending(false);
      pushNotice("Suggestion request failed. Try again.", "error");
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
    pushNotice("Clip created. Render started.", "success");
    return clip;
  };

  const handleSuggest = () => {
    suggestMutation.mutate();
    pushNotice("Generating suggestions...", "info");
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
      pushNotice("Suggestion accepted. Preview render started.", "success");
    } catch (err) {
      setError(isSafeError(err));
    } finally {
      setClipActionLoading(suggestion.id, false);
    }
  };

  const handleRender = async (suggestion, renderType) => {
    setClipActionLoading(suggestion.id, true);
    if (renderType === "preview") {
      setPreviewClip(null);
    }
    try {
      if (renderType === "preview") {
        const previewReady =
          suggestion.render_type === "preview" &&
          suggestion.status === "done" &&
          (suggestion.download_url || suggestion.output_url);
        if (previewReady) {
          setPreviewClip(suggestion);
          pushNotice("Preview ready.", "success");
          return;
        }
        const previewQueued =
          suggestion.render_type === "preview" &&
          (suggestion.status === "pending" || suggestion.status === "processing");
        if (previewQueued) {
          pushNotice("Preview rendering...", "info");
          const clip = await pollClipUntilReady(suggestion.id);
          if (clip) {
            setPreviewClip(clip);
          } else {
            pushNotice("Preview render timed out. Try again.", "error");
          }
          return;
        }
      }

      const clipId =
        renderType === "preview"
          ? suggestion.id
          : await getOrCreateManualClipId(suggestion);
      await renderClip(clipId, renderType);
      await queryClient.invalidateQueries({ queryKey: ["clips", sermonId] });
      if (renderType === "preview") {
        await queryClient.invalidateQueries({ queryKey: ["suggestions", sermonId] });
      }
      pushNotice(
        renderType === "preview"
          ? "Preview render started."
          : "Final render started.",
        "success"
      );
      if (renderType === "preview") {
        const clip = await pollClipUntilReady(clipId);
        if (clip) {
          setPreviewClip(clip);
        } else {
          pushNotice("Preview render timed out. Try again.", "error");
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
      pushNotice("Trim applied to suggestion.", "success");
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
      pushNotice("Suggestion rejected.", "info");
    } catch (err) {
      setError(isSafeError(err));
    } finally {
      setClipActionLoading(suggestion.id, false);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-8 px-6 py-16">
      <nav
        aria-label="Breadcrumb"
        className="flex flex-wrap items-center gap-2 text-xs text-slate-500"
      >
        <Link href="/app" className="hover:text-slate-300">
          App
        </Link>
        <span className="text-slate-700">/</span>
        <span className="text-slate-500">Sermons</span>
        <span className="text-slate-700">/</span>
        <span className="text-slate-300">
          {sermon?.title || `Sermon #${sermonId}`}
        </span>
      </nav>

      {notice ? (
        <div className={`rounded-2xl border px-4 py-3 text-sm ${NOTICE_STYLES[notice.tone]}`}>
          <div className="flex items-start justify-between gap-4">
            <span>{notice.message}</span>
            <button
              type="button"
              onClick={() => setNotice(null)}
              className="text-xs uppercase tracking-wide text-slate-400 hover:text-slate-200"
            >
              Dismiss
            </button>
          </div>
        </div>
      ) : null}

      {previewClip ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-4 py-6"
          onClick={() => setPreviewClip(null)}
        >
          <div
            className="w-full max-w-4xl rounded-2xl border border-slate-800 bg-slate-950 p-4 shadow-xl max-h-[85vh] overflow-y-auto"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-slate-100">
                  Suggested clip preview
                </p>
                <p className="text-xs text-slate-500">
                  Start {formatTimestamp(previewClip.start_ms)} - End{" "}
                  {formatTimestamp(previewClip.end_ms)}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setPreviewClip(null)}
                className="rounded-full border border-slate-800 px-3 py-1 text-xs text-slate-300 hover:border-slate-600"
              >
                Close
              </button>
            </div>
            {previewUrl ? (
              <div className="mt-4">
                <video
                  controls
                  preload="metadata"
                  className="w-full max-h-[60vh] rounded-xl border border-slate-800 bg-slate-950 object-contain"
                  src={previewUrl}
                />
              </div>
            ) : (
              <div className="mt-4 rounded-xl border border-dashed border-slate-800 px-4 py-10 text-sm text-slate-500">
                Preview is not available yet.
              </div>
            )}
            {previewUrl ? (
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <a
                  href={previewUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-full border border-slate-700 px-4 py-2 text-xs text-slate-200 hover:border-slate-500"
                >
                  Open in new tab
                </a>
                <a
                  href={previewUrl}
                  download
                  className="rounded-full border border-emerald-500/50 px-4 py-2 text-xs text-emerald-200 hover:border-emerald-400"
                >
                  Download
                </a>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-slate-400">
            Sermon detail
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold text-slate-100">
              {sermon?.title || `Sermon #${sermonId}`}
            </h1>
            {sermon?.status ? (
              <span className="rounded-full border border-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
                {sermon.status}
              </span>
            ) : null}
          </div>
          <p className="text-sm text-slate-500">{sermon?.status || "loading"}</p>
        </div>
        <Link
          href="/app"
          className="rounded-full border border-slate-800 px-4 py-2 text-sm text-slate-300 hover:border-slate-700"
        >
          Back
        </Link>
      </div>

      <section className="rounded-2xl border border-slate-800 bg-slate-950/50 p-6">
        <p className="text-sm text-slate-400">Status</p>
        {loading ? (
          <div className="mt-4 flex items-center gap-3 text-sm text-slate-400">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-700 border-t-emerald-400" />
            Loading status...
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
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-slate-200">Sermon preview</p>
            <p className="text-xs text-slate-500">
              Watch the original upload before clipping.
            </p>
          </div>
          {sermonSourceUrl ? (
            <a
              href={sermonSourceUrl}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-emerald-300 hover:text-emerald-200"
            >
              Open video
            </a>
          ) : null}
        </div>
        <div className="mt-4">
          {sermonSourceUrl ? (
            <video
              controls
              preload="metadata"
              className="w-full rounded-xl border border-slate-800 bg-slate-950"
              src={sermonSourceUrl}
            />
          ) : (
            <div className="flex items-center justify-center rounded-xl border border-dashed border-slate-800 bg-slate-950/70 px-4 py-10 text-sm text-slate-500">
              No video source available yet.
            </div>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-950/50 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-slate-200">Workflow</p>
            <p className="text-xs text-slate-500">
              Track progress across transcription, suggestions, and renders.
            </p>
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {workflowCards.map((card) => {
            const meta = getWorkflowMeta(card.state);
            return (
              <div
                key={card.title}
                className="rounded-xl border border-slate-800 bg-slate-950/60 p-4"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-100">{card.title}</p>
                  <span
                    className={`inline-flex items-center gap-2 rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wide ${meta.badge}`}
                  >
                    <span className={`h-2 w-2 rounded-full ${meta.dot}`} />
                    {meta.label}
                  </span>
                </div>
                <p className="mt-2 text-xs text-slate-500">{card.detail}</p>
                {card.title === "Transcription" && progress !== null ? (
                  <div className="mt-3 h-1.5 w-full rounded-full bg-slate-900">
                    <div
                      className="h-1.5 rounded-full bg-emerald-500/70"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
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
                    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                      <span className="rounded-full border border-slate-800 px-2 py-0.5">
                        Start {formatTimestamp(result.start_ms)}
                      </span>
                      <span className="rounded-full border border-slate-800 px-2 py-0.5">
                        End {formatTimestamp(result.end_ms)}
                      </span>
                    </div>
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

      <section className="rounded-2xl border border-slate-800 bg-slate-950/50 px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-slate-200">Transcript</p>
            <p className="text-xs text-slate-500">
              Expand to select segments and create a clip.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setIsTranscriptOpen((prev) => !prev)}
            className="rounded-full border border-slate-800 px-3 py-1 text-xs text-slate-300 hover:border-slate-700"
          >
            {isTranscriptOpen ? "Hide transcript" : "Show transcript"}
          </button>
        </div>
      </section>

      {isTranscriptOpen ? (
        <ClipBuilder
          title="Transcript"
          subtitle="Select a start segment and an end segment."
          segments={segments}
          mediaUrl={sermonSourceUrl}
          initialStartMs={jumpTarget?.start_ms ?? null}
          initialEndMs={jumpTarget?.end_ms ?? null}
          actionLabel="Create clip"
          busyLabel="Creating..."
          onSubmit={({ start_ms, end_ms }) =>
            handleCreateClip({ start_ms, end_ms, render_type: "final" })
          }
        />
      ) : null}

      <SuggestedClipsPanel
        useLlmSuggestions={useLlmSuggestions}
        onToggleUseLlm={setUseLlmSuggestions}
        onSuggest={handleSuggest}
        suggesting={suggesting}
        suggestionsLoading={suggestionsLoading}
        suggestionsError={suggestionsErrorMessage}
        suggestionsPending={suggestionsPending}
        suggestionsProgress={suggestionsProgress}
        suggestionsProgressLabel={suggestionsProgressLabel}
        suggestionsShowProgress={suggestionsPending || warmupPending}
        suggestionsLocked={suggestionsLocked}
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
          mediaUrl={sermonSourceUrl}
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
