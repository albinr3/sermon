"use client";

import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient
} from "@tanstack/react-query";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  acceptSuggestion,
  applyTrimSuggestion,
  createClip,
  deleteSermon,
  deleteSuggestions,
  generateEmbeddings,
  getClip,
  getSermon,
  getTokenStats,
  getTranscriptStats,
  getTranscriptSegments,
  listClips,
  listSuggestions,
  recordClipFeedback,
  renderClip,
  searchSermon,
  suggestClips,
  updateSermon
} from "../../../../lib/api";

const ClipBuilder = dynamic(() => import("./components/ClipBuilder"), {
  loading: () => (
    <section className="surface-card">
      <div className="h-48 animate-pulse rounded-2xl bg-[color:var(--bg-elevated)]" />
    </section>
  )
});

const SuggestedClipsPanel = dynamic(
  () => import("./components/SuggestedClipsPanel"),
  {
    loading: () => (
      <section className="surface-card p-6">
        <div className="h-6 w-48 animate-pulse rounded bg-[color:var(--bg-elevated)]" />
      </section>
    )
  }
);

const POLL_INTERVAL_MS = Number(process.env.NEXT_PUBLIC_POLL_INTERVAL_MS) || 5000;
const ACTIVE_STATUSES = new Set(["pending", "processing", "uploaded"]);
const CLIP_ACTIVE_STATUSES = new Set(["pending", "processing"]);
const PREVIEW_WARMUP_COUNT = 1;
const SEGMENTS_PAGE_SIZE = 200;
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
    badge:
      "border-[color:var(--accent-2)] bg-[color:var(--accent-2-soft)] text-[color:var(--accent-2-strong)]",
    dot: "bg-[color:var(--accent-2)]"
  },
  active: {
    label: "In progress",
    badge: "border-[#f2c37a] bg-[#f7e5c7] text-[#7a4a12]",
    dot: "bg-[color:var(--honey)]"
  },
  idle: {
    label: "Ready",
    badge: "border-[color:var(--line)] bg-[color:var(--surface-soft)] text-[color:var(--muted)]",
    dot: "bg-[color:var(--line)]"
  },
  blocked: {
    label: "Waiting",
    badge: "border-[color:var(--line)] bg-transparent text-[color:var(--muted)]",
    dot: "bg-[color:var(--line)]"
  },
  error: {
    label: "Error",
    badge: "border-[#e6b1aa] bg-[#fbe2e0] text-[#8c2f26]",
    dot: "bg-[#d4574a]"
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

function parseTagsInput(value) {
  if (!value) return [];
  const tags = value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
  return Array.from(new Set(tags));
}

const NOTICE_STYLES = {
  info: "border-[color:var(--line)] bg-[color:var(--surface-soft)] text-[color:var(--ink)]",
  success:
    "border-[color:var(--accent-2)] bg-[color:var(--accent-2-soft)] text-[color:var(--accent-2-strong)]",
  error: "border-[#e6b1aa] bg-[#fbe2e0] text-[#8c2f26]"
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
  const router = useRouter();
  const [error, setError] = useState("");
  const [suggestionsPending, setSuggestionsPending] = useState(false);
  const [suggestionsError, setSuggestionsError] = useState("");
  const [useLlmSuggestions, setUseLlmSuggestions] = useState(
    process.env.NEXT_PUBLIC_DEFAULT_USE_LLM_FOR_CLIPS === "true"
  );
  const [llmMethod, setLlmMethod] = useState("scoring");
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
  const [metadataDraft, setMetadataDraft] = useState({
    title: "",
    description: "",
    preacher: "",
    series: "",
    sermon_date: "",
    tags: ""
  });
  const [metadataDirty, setMetadataDirty] = useState(false);
  const [metadataError, setMetadataError] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [tokenStats, setTokenStats] = useState(null);
  const [tokenStatsOpen, setTokenStatsOpen] = useState(false);
  const [tokenStatsLoading, setTokenStatsLoading] = useState(false);
  const [tokenStatsError, setTokenStatsError] = useState("");

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
    setLlmMethod("scoring");
    setMetadataDraft({
      title: "",
      description: "",
      preacher: "",
      series: "",
      sermon_date: "",
      tags: ""
    });
    setMetadataDirty(false);
    setMetadataError("");
    setDeleteError("");
    setTokenStats(null);
    setTokenStatsOpen(false);
    setTokenStatsLoading(false);
    setTokenStatsError("");
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
    },
    staleTime: 10_000,
    gcTime: 5 * 60 * 1000
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

  useEffect(() => {
    if (!sermon || metadataDirty) {
      return;
    }
    setMetadataDraft({
      title: sermon.title || "",
      description: sermon.description || "",
      preacher: sermon.preacher || "",
      series: sermon.series || "",
      sermon_date: sermon.sermon_date || "",
      tags: Array.isArray(sermon.tags) ? sermon.tags.join(", ") : ""
    });
  }, [sermon, metadataDirty]);

  const shouldLoadSegments =
    Boolean(sermon) &&
    ["transcribed", "suggested", "completed", "embedded"].includes(
      sermon.status
    ) &&
    (isTranscriptOpen || Boolean(editingSuggestion) || Boolean(jumpTarget));

  const segmentsQuery = useInfiniteQuery({
    queryKey: ["segments", sermonId],
    queryFn: ({ pageParam = 0 }) =>
      getTranscriptSegments(sermonId, {
        offset: pageParam,
        limit: SEGMENTS_PAGE_SIZE
      }),
    getNextPageParam: (lastPage, pages) =>
      lastPage.length < SEGMENTS_PAGE_SIZE
        ? undefined
        : pages.length * SEGMENTS_PAGE_SIZE,
    enabled: shouldLoadSegments,
    staleTime: 60_000,
    gcTime: 10 * 60 * 1000
  });
  const segments = segmentsQuery.data?.pages.flat() || [];
  const segmentsLoading = segmentsQuery.isLoading;
  const segmentsLoadingMore = segmentsQuery.isFetchingNextPage;

  const transcriptStatsQuery = useQuery({
    queryKey: ["transcript-stats", sermonId],
    queryFn: () => getTranscriptStats(sermonId),
    enabled: Boolean(sermonId) && isTranscriptOpen,
    staleTime: 60_000,
    gcTime: 5 * 60 * 1000
  });
  const transcriptWordCount = transcriptStatsQuery.data?.word_count ?? null;
  const transcriptCharCount = transcriptStatsQuery.data?.char_count ?? null;

  useEffect(() => {
    if (!segmentsQuery.hasNextPage || segmentsQuery.isFetchingNextPage) {
      return;
    }
    const targetEndMs = editingSuggestion?.end_ms ?? jumpTarget?.end_ms ?? null;
    if (!targetEndMs || segments.length === 0) {
      return;
    }
    const lastEndMs = segments[segments.length - 1]?.end_ms ?? null;
    if (lastEndMs !== null && targetEndMs > lastEndMs) {
      segmentsQuery.fetchNextPage();
    }
  }, [
    editingSuggestion,
    jumpTarget,
    segments,
    segmentsQuery.hasNextPage,
    segmentsQuery.isFetchingNextPage,
    segmentsQuery.fetchNextPage
  ]);

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

  const metadataMutation = useMutation({
    mutationFn: (payload) => updateSermon(sermonId, payload),
    onSuccess: (data) => {
      queryClient.setQueryData(["sermon", sermonId], data);
      queryClient.invalidateQueries({ queryKey: ["sermons"] });
      setMetadataDraft({
        title: data.title || "",
        description: data.description || "",
        preacher: data.preacher || "",
        series: data.series || "",
        sermon_date: data.sermon_date || "",
        tags: Array.isArray(data.tags) ? data.tags.join(", ") : ""
      });
      setMetadataDirty(false);
      setMetadataError("");
      pushNotice("Metadata saved.", "success");
    },
    onError: (err) => {
      const message = isSafeError(err);
      setMetadataError(message);
      pushNotice("Metadata save failed.", "error");
    }
  });
  const metadataSaving = metadataMutation.isPending;

  const deleteMutation = useMutation({
    mutationFn: () => deleteSermon(sermonId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sermons"] });
      queryClient.removeQueries({ queryKey: ["sermon", sermonId] });
      router.push("/app");
    },
    onError: (err) => {
      const message = isSafeError(err);
      setDeleteError(message);
      pushNotice("Delete failed.", "error");
    }
  });
  const deletePending = deleteMutation.isPending;

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

  const updateMetadataField = (field) => (event) => {
    setMetadataDraft((prev) => ({ ...prev, [field]: event.target.value }));
    setMetadataDirty(true);
  };

  const handleMetadataReset = () => {
    if (!sermon) return;
    setMetadataDraft({
      title: sermon.title || "",
      description: sermon.description || "",
      preacher: sermon.preacher || "",
      series: sermon.series || "",
      sermon_date: sermon.sermon_date || "",
      tags: Array.isArray(sermon.tags) ? sermon.tags.join(", ") : ""
    });
    setMetadataDirty(false);
    setMetadataError("");
  };

  const handleMetadataSave = () => {
    if (!sermon || metadataSaving) return;
    setMetadataError("");
    const payload = {
      title: metadataDraft.title.trim() || null,
      description: metadataDraft.description.trim() || null,
      preacher: metadataDraft.preacher.trim() || null,
      series: metadataDraft.series.trim() || null,
      sermon_date: metadataDraft.sermon_date || null,
      tags: parseTagsInput(metadataDraft.tags)
    };
    metadataMutation.mutate(payload);
  };

  const handleDelete = () => {
    if (!sermon || deletePending) return;
    const confirmed = window.confirm(
      "Delete this sermon? This will hide the sermon and related data."
    );
    if (!confirmed) return;
    setDeleteError("");
    deleteMutation.mutate();
  };

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
    mutationFn: () => suggestClips(sermonId, useLlmSuggestions, llmMethod),
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

  const handleDeleteSuggestions = async () => {
    if (suggestionsLocked || suggesting) {
      return;
    }
    const confirmed = window.confirm(
      "Delete all suggested clips for this sermon?"
    );
    if (!confirmed) {
      return;
    }
    try {
      await deleteSuggestions(sermonId);
      await queryClient.invalidateQueries({ queryKey: ["suggestions", sermonId] });
      setSuggestionsPending(false);
      pushNotice("Suggestions deleted.", "success");
    } catch (err) {
      setSuggestionsError(isSafeError(err));
      pushNotice("Failed to delete suggestions.", "error");
    }
  };

  const loadTokenStats = async () => {
    if (tokenStatsLoading) {
      return;
    }
    setTokenStatsError("");
    setTokenStatsLoading(true);
    try {
      const data = await getTokenStats(sermonId);
      setTokenStats(data);
    } catch (err) {
      setTokenStatsError(isSafeError(err));
    } finally {
      setTokenStatsLoading(false);
    }
  };

  const handleToggleTokenStats = async () => {
    if (tokenStatsOpen) {
      setTokenStatsOpen(false);
      return;
    }
    setTokenStatsOpen(true);
    if (!tokenStats) {
      await loadTokenStats();
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
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-10 px-6 py-14">
      <nav
        aria-label="Breadcrumb"
        className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--muted)]"
      >
        <Link href="/app" className="hover:text-[color:var(--accent-strong)]">
          App
        </Link>
        <span className="text-[color:var(--line)]">/</span>
        <span className="text-[color:var(--muted)]">Sermons</span>
        <span className="text-[color:var(--line)]">/</span>
        <span className="text-[color:var(--ink)]">
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
              className="text-xs uppercase tracking-wide text-[color:var(--muted)] hover:text-[color:var(--ink)]"
            >
              Dismiss
            </button>
          </div>
        </div>
      ) : null}

      {previewClip ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#1f1a16]/70 px-4 py-6"
          onClick={() => setPreviewClip(null)}
        >
          <div
            className="w-full max-w-4xl rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface)] p-4 shadow-xl max-h-[85vh] overflow-y-auto"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-[color:var(--ink)]">
                  Suggested clip preview
                </p>
                <p className="text-xs text-[color:var(--muted)]">
                  Start {formatTimestamp(previewClip.start_ms)} - End{" "}
                  {formatTimestamp(previewClip.end_ms)}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setPreviewClip(null)}
                className="btn btn-outline px-3 py-1 text-xs"
              >
                Close
              </button>
            </div>
            {previewUrl ? (
              <div className="mt-4">
                <video
                  controls
                  preload="metadata"
                  className="w-full max-h-[60vh] rounded-xl border border-[color:var(--line)] bg-[color:var(--bg-elevated)] object-contain"
                  src={previewUrl}
                />
              </div>
            ) : (
              <div className="mt-4 rounded-xl border border-dashed border-[color:var(--line)] px-4 py-10 text-sm text-[color:var(--muted)]">
                Preview is not available yet.
              </div>
            )}
            {previewUrl ? (
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <a
                  href={previewUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-outline px-4 py-2 text-xs"
                >
                  Open in new tab
                </a>
                <a
                  href={previewUrl}
                  download
                  className="btn btn-primary px-4 py-2 text-xs"
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
          <span className="pill">Sermon detail</span>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h1 className="text-3xl">
              {sermon?.title || `Sermon #${sermonId}`}
            </h1>
            {sermon?.status ? (
              <span className="rounded-full border border-[color:var(--line)] px-2 py-0.5 text-[10px] uppercase tracking-wide text-[color:var(--muted)]">
                {sermon.status}
              </span>
            ) : null}
          </div>
          <p className="text-sm text-[color:var(--muted)]">
            {sermon?.status || "loading"}
          </p>
        </div>
        <Link href="/app" className="btn btn-outline">
          Back
        </Link>
      </div>

      <section className="surface-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">Metadata</p>
            <p className="text-xs text-[color:var(--muted)]">
              Update title, description, preacher, date, and tags.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleMetadataReset}
              disabled={!metadataDirty || metadataSaving || !sermon}
              className="btn btn-outline px-3 py-1 text-xs disabled:opacity-50"
            >
              Reset
            </button>
            <button
              type="button"
              onClick={handleMetadataSave}
              disabled={!metadataDirty || metadataSaving || !sermon}
              className="btn btn-primary px-3 py-1 text-xs disabled:opacity-50"
            >
              {metadataSaving ? "Saving..." : "Save metadata"}
            </button>
          </div>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="flex flex-col gap-2 text-xs uppercase tracking-wide text-[color:var(--muted)]">
            Title
            <input
              type="text"
              value={metadataDraft.title}
              onChange={updateMetadataField("title")}
              className="rounded-xl border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2 text-sm normal-case text-[color:var(--ink)] placeholder:text-[color:var(--muted)] focus:border-[color:var(--accent)] focus:outline-none"
              disabled={!sermon || metadataSaving}
              placeholder="Sermon title"
            />
          </label>
          <label className="flex flex-col gap-2 text-xs uppercase tracking-wide text-[color:var(--muted)]">
            Preacher
            <input
              type="text"
              value={metadataDraft.preacher}
              onChange={updateMetadataField("preacher")}
              className="rounded-xl border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2 text-sm normal-case text-[color:var(--ink)] placeholder:text-[color:var(--muted)] focus:border-[color:var(--accent)] focus:outline-none"
              disabled={!sermon || metadataSaving}
              placeholder="Speaker name"
            />
          </label>
          <label className="flex flex-col gap-2 text-xs uppercase tracking-wide text-[color:var(--muted)]">
            Date
            <input
              type="date"
              value={metadataDraft.sermon_date}
              onChange={updateMetadataField("sermon_date")}
              className="rounded-xl border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2 text-sm normal-case text-[color:var(--ink)] focus:border-[color:var(--accent)] focus:outline-none"
              disabled={!sermon || metadataSaving}
            />
          </label>
          <label className="flex flex-col gap-2 text-xs uppercase tracking-wide text-[color:var(--muted)]">
            Series
            <input
              type="text"
              value={metadataDraft.series}
              onChange={updateMetadataField("series")}
              className="rounded-xl border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2 text-sm normal-case text-[color:var(--ink)] placeholder:text-[color:var(--muted)] focus:border-[color:var(--accent)] focus:outline-none"
              disabled={!sermon || metadataSaving}
              placeholder="Series name"
            />
          </label>
        </div>
        <label className="mt-4 flex flex-col gap-2 text-xs uppercase tracking-wide text-[color:var(--muted)]">
          Description
          <textarea
            value={metadataDraft.description}
            onChange={updateMetadataField("description")}
            className="min-h-[96px] rounded-xl border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2 text-sm normal-case text-[color:var(--ink)] placeholder:text-[color:var(--muted)] focus:border-[color:var(--accent)] focus:outline-none"
            disabled={!sermon || metadataSaving}
            placeholder="Notes about this sermon"
          />
        </label>
        <label className="mt-4 flex flex-col gap-2 text-xs uppercase tracking-wide text-[color:var(--muted)]">
          Tags
          <input
            type="text"
            value={metadataDraft.tags}
            onChange={updateMetadataField("tags")}
            className="rounded-xl border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2 text-sm normal-case text-[color:var(--ink)] placeholder:text-[color:var(--muted)] focus:border-[color:var(--accent)] focus:outline-none"
            disabled={!sermon || metadataSaving}
            placeholder="faith, hope, outreach"
          />
          <span className="text-[10px] text-[color:var(--muted)]">
            Separate tags with commas.
          </span>
        </label>
        {metadataError ? (
          <p className="mt-3 text-sm text-[#a33a2b]">{metadataError}</p>
        ) : null}
        {metadataDirty && !metadataSaving ? (
          <p className="mt-3 text-xs text-[color:var(--muted)]">
            Unsaved changes.
          </p>
        ) : null}
      </section>

      <section className="surface-card p-6">
        <p className="text-sm text-[color:var(--muted)]">Status</p>
        {loading ? (
          <div className="mt-4 flex items-center gap-3 text-sm text-[color:var(--muted)]">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-[color:var(--line)] border-t-[color:var(--accent)]" />
            Loading status...
          </div>
        ) : statusError ? (
          <p className="mt-2 text-sm text-[#a33a2b]">{statusError}</p>
        ) : (
          <div className="mt-2 space-y-2">
            <p className="text-lg font-semibold text-[color:var(--ink)]">
              {sermon?.status}
            </p>
            {progress !== null ? (
              <div className="space-y-1">
                <div className="h-2 w-full max-w-xs rounded-full bg-[color:var(--bg-elevated)]">
                  <div
                    className="h-2 rounded-full bg-[color:var(--accent)]"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="text-xs text-[color:var(--muted)]">{progress}%</p>
              </div>
            ) : null}
            {sermon?.error_message ? (
              <p className="text-sm text-[#a33a2b]">{sermon.error_message}</p>
            ) : null}
          </div>
        )}
      </section>

      <section className="surface-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">Sermon preview</p>
            <p className="text-xs text-[color:var(--muted)]">
              Watch the original upload before clipping.
            </p>
          </div>
          {sermonSourceUrl ? (
            <a
              href={sermonSourceUrl}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-[color:var(--accent-strong)] hover:text-[color:var(--accent)]"
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
              className="w-full rounded-xl border border-[color:var(--line)] bg-[color:var(--bg-elevated)]"
              src={sermonSourceUrl}
            />
          ) : (
            <div className="flex items-center justify-center rounded-xl border border-dashed border-[color:var(--line)] bg-[color:var(--surface-soft)] px-4 py-10 text-sm text-[color:var(--muted)]">
              No video source available yet.
            </div>
          )}
        </div>
      </section>

      <section className="surface-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">Workflow</p>
            <p className="text-xs text-[color:var(--muted)]">
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
                className="surface-card-soft p-4"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">{card.title}</p>
                  <span
                    className={`inline-flex items-center gap-2 rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wide ${meta.badge}`}
                  >
                    <span className={`h-2 w-2 rounded-full ${meta.dot}`} />
                    {meta.label}
                  </span>
                </div>
                <p className="mt-2 text-xs text-[color:var(--muted)]">
                  {card.detail}
                </p>
                {card.title === "Transcription" && progress !== null ? (
                  <div className="mt-3 h-1.5 w-full rounded-full bg-[color:var(--bg-elevated)]">
                    <div
                      className="h-1.5 rounded-full bg-[color:var(--accent)]"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </section>

      <section className="surface-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold">Semantic Search</p>
            <p className="text-xs text-[color:var(--muted)]">
              Find moments by meaning, not exact words.
            </p>
          </div>
          {sermon?.status !== "embedded" ? (
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={requestEmbeddings}
                disabled={embeddingLoading}
                className="btn btn-outline px-4 py-2 text-xs disabled:opacity-50"
              >
                {embeddingLoading ? "Generating..." : "Generate embeddings"}
              </button>
              {embeddingRequested ? (
                <span className="text-xs text-[color:var(--muted)]">
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
            className="w-full rounded-xl border border-[color:var(--line)] bg-[color:var(--surface)] px-4 py-3 text-sm text-[color:var(--ink)] placeholder:text-[color:var(--muted)] focus:border-[color:var(--accent)] focus:outline-none"
          />
        </div>
        <div className="mt-4 space-y-3">
          {embeddingError ? (
            <p className="text-sm text-[#a33a2b]">{embeddingError}</p>
          ) : sermon?.status !== "embedded" ? (
            <p className="text-sm text-[color:var(--muted)]">
              Embeddings are required for semantic search.{" "}
              {embeddingRequested ? "Generating them now..." : "Click to generate."}
            </p>
          ) : searchLoading ? (
            <div className="space-y-2">
              <div className="h-4 w-2/3 animate-pulse rounded bg-[color:var(--bg-elevated)]" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-[color:var(--bg-elevated)]" />
            </div>
          ) : searchError ? (
            <p className="text-sm text-[#a33a2b]">{searchError}</p>
          ) : !hasSearchInput ? (
            <p className="text-sm text-[color:var(--muted)]">Type to search.</p>
          ) : searchResults.length === 0 ? (
            <p className="text-sm text-[color:var(--muted)]">No matches yet.</p>
          ) : (
            searchResults.map((result) => (
              <div
                key={result.segment_id}
                className="surface-card-soft p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--muted)]">
                      <span className="rounded-full border border-[color:var(--line)] px-2 py-0.5">
                        Start {formatTimestamp(result.start_ms)}
                      </span>
                      <span className="rounded-full border border-[color:var(--line)] px-2 py-0.5">
                        End {formatTimestamp(result.end_ms)}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-[color:var(--ink)]">
                      {result.text}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      setJumpTarget({
                        start_ms: result.start_ms,
                        end_ms: result.end_ms
                      })
                    }
                    className="btn btn-outline px-3 py-1 text-xs"
                  >
                    Jump
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="surface-card px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">Transcript</p>
            <p className="text-xs text-[color:var(--muted)]">
              Expand to select segments and create a clip.
            </p>
            {isTranscriptOpen ? (
              <p className="text-xs text-[color:var(--muted)]">
                {transcriptStatsQuery.isLoading
                  ? "Counting words..."
                  : transcriptWordCount !== null
                  ? `Total words: ${transcriptWordCount.toLocaleString()}`
                  : "Total words: unavailable"}
                {transcriptStatsQuery.isLoading
                  ? ""
                  : transcriptCharCount !== null
                  ? ` · Total characters: ${transcriptCharCount.toLocaleString()}`
                  : " · Total characters: unavailable"}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={() => setIsTranscriptOpen((prev) => !prev)}
            className="btn btn-outline px-3 py-1 text-xs"
          >
            {isTranscriptOpen ? "Hide transcript" : "Show transcript"}
          </button>
        </div>
      </section>

      {isTranscriptOpen ? (
        <>
          <section className="surface-card-soft px-6 py-3">
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-[color:var(--muted)]">
              <span>
                {segmentsLoading && segments.length === 0
                  ? "Loading transcript..."
                  : `${segments.length} segments loaded`}
              </span>
              {segmentsQuery.hasNextPage ? (
                <button
                  type="button"
                  onClick={() => segmentsQuery.fetchNextPage()}
                  disabled={segmentsLoadingMore}
                  className="btn btn-outline px-3 py-1 text-xs disabled:opacity-50"
                >
                  {segmentsLoadingMore ? "Loading..." : "Load more"}
                </button>
              ) : segments.length > 0 ? (
                <span className="text-[10px] uppercase tracking-wide text-[color:var(--muted)]">
                  All segments loaded
                </span>
              ) : null}
            </div>
          </section>
          {segmentsLoading && segments.length === 0 ? (
            <section className="surface-card p-6">
              <div className="flex items-center gap-3 text-sm text-[color:var(--muted)]">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-[color:var(--line)] border-t-[color:var(--accent)]" />
                Loading transcript...
              </div>
            </section>
          ) : (
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
          )}
        </>
      ) : null}

      <SuggestedClipsPanel
        useLlmSuggestions={useLlmSuggestions}
        onToggleUseLlm={setUseLlmSuggestions}
        llmMethod={llmMethod}
        onSelectLlmMethod={setLlmMethod}
        onSuggest={handleSuggest}
        onDeleteSuggestions={handleDeleteSuggestions}
        onToggleTokenStats={handleToggleTokenStats}
        tokenStats={tokenStats}
        tokenStatsOpen={tokenStatsOpen}
        tokenStatsLoading={tokenStatsLoading}
        tokenStatsError={tokenStatsError}
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
        segmentsLoading && segments.length === 0 ? (
          <section className="surface-card p-6">
            <div className="flex items-center gap-3 text-sm text-[color:var(--muted)]">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-[color:var(--line)] border-t-[color:var(--accent)]" />
              Loading transcript...
            </div>
          </section>
        ) : (
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
        )
      ) : null}

      <section className="surface-card">
        <div className="border-b border-[color:var(--line)] px-6 py-4">
          <p className="text-sm font-semibold">Clips</p>
        </div>
        <div className="divide-y divide-[color:var(--line)] px-6 py-4">
          {clipsLoading ? (
            <div className="space-y-3">
              <div className="h-6 w-48 animate-pulse rounded bg-[color:var(--bg-elevated)]" />
              <div className="h-6 w-40 animate-pulse rounded bg-[color:var(--bg-elevated)]" />
            </div>
          ) : clips.length === 0 ? (
            <p className="text-sm text-[color:var(--muted)]">No clips yet.</p>
          ) : (
            clips.map((clip) => (
              <div key={clip.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm text-[color:var(--ink)]">
                    {Math.round((clip.end_ms - clip.start_ms) / 1000)}s clip
                  </p>
                  <p className="text-xs text-[color:var(--muted)]">
                    {formatClipStatus(clip.status)}
                  </p>
                </div>
                {clip.status === "done" ? (
                  <a
                    href={clip.download_url || clip.output_url || "#"}
                    className="text-sm text-[color:var(--accent-strong)] hover:text-[color:var(--accent)]"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Download
                  </a>
                ) : (
                  <span className="text-xs text-[color:var(--muted)]">
                    {formatClipStatus(clip.status)}
                  </span>
                )}
              </div>
            ))
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-[#e6b1aa] bg-[#fbe2e0] p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-[#8c2f26]">Danger zone</p>
            <p className="text-xs text-[#8c2f26]/80">
              Delete hides this sermon, clips, and transcript data.
            </p>
          </div>
          <button
            type="button"
            onClick={handleDelete}
            disabled={!sermon || deletePending}
            className="btn btn-danger px-4 py-2 text-xs disabled:opacity-50"
          >
            {deletePending ? "Deleting..." : "Delete sermon"}
          </button>
        </div>
        {deleteError ? (
          <p className="mt-3 text-sm text-[#8c2f26]">{deleteError}</p>
        ) : null}
      </section>
    </main>
  );
}
