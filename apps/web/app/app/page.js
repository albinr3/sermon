"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";

import { listSermons } from "../../lib/api";

const POLL_INTERVAL_MS = Number(process.env.NEXT_PUBLIC_POLL_INTERVAL_MS) || 5000;
const ACTIVE_STATUSES = new Set(["pending", "uploaded", "processing"]);
const LOADING_ROWS = 3;
const SERMONS_PAGE_SIZE = 25;

const UploadSermon = dynamic(() => import("../components/UploadSermon"), {
  loading: () => (
    <div className="h-10 w-40 animate-pulse rounded-xl bg-[color:var(--bg-elevated)]" />
  )
});

const formatStatus = (status) => {
  if (!status) return "Unknown";
  return `${status.charAt(0).toUpperCase()}${status.slice(1)}`;
};

export default function Home() {
  const [searchText, setSearchText] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [tagFilter, setTagFilter] = useState("");
  const normalizedSearch = searchText.trim();

  useEffect(() => {
    if (!normalizedSearch) {
      setDebouncedSearch("");
      return;
    }
    const timeout = setTimeout(() => setDebouncedSearch(normalizedSearch), 300);
    return () => clearTimeout(timeout);
  }, [normalizedSearch]);

  const sermonsQuery = useInfiniteQuery({
    queryKey: ["sermons", debouncedSearch, statusFilter, tagFilter],
    queryFn: ({ pageParam = 0 }) =>
      listSermons({
        limit: SERMONS_PAGE_SIZE,
        offset: pageParam,
        q: debouncedSearch || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        tag: tagFilter.trim() || undefined
      }),
    getNextPageParam: (lastPage, pages) =>
      lastPage.length < SERMONS_PAGE_SIZE
        ? undefined
        : pages.length * SERMONS_PAGE_SIZE,
    refetchInterval: (query) => {
      const pages = query.state.data?.pages || [];
      const sermons = pages.flat();
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
    },
    staleTime: 10_000,
    gcTime: 5 * 60 * 1000
  });

  const sermons = sermonsQuery.data?.pages.flat() || [];
  const error = sermonsQuery.error?.message || "";
  const loading = sermonsQuery.isLoading;
  const loadingMore = sermonsQuery.isFetchingNextPage;
  const fetching = sermonsQuery.isFetching;
  const hasNextPage = sermonsQuery.hasNextPage;
  const hasFilters =
    normalizedSearch.length > 0 ||
    statusFilter !== "all" ||
    tagFilter.trim().length > 0;
  const tagOptions = Array.from(
    new Set(
      sermons.flatMap((sermon) => (Array.isArray(sermon.tags) ? sermon.tags : []))
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0)
    )
  ).sort((a, b) => a.localeCompare(b));
  const statusOptions = Array.from(
    new Set(sermons.map((sermon) => sermon.status).filter(Boolean))
  ).sort((a, b) => a.localeCompare(b));

  const clearFilters = () => {
    setSearchText("");
    setStatusFilter("all");
    setTagFilter("");
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-10 px-6 py-14">
      <header className="space-y-3">
        <span className="pill w-fit">SermonClip Studio</span>
        <h1 className="text-4xl">Sermon clip workspace</h1>
        <p className="text-[color:var(--muted)]">
          Upload sermons, track processing, and build clips in one place.
        </p>
      </header>

      <section className="surface-card flex flex-wrap items-center justify-between gap-4 p-6">
        <div>
          <p className="text-lg font-semibold">Uploads</p>
          <p className="text-sm text-[color:var(--muted)]">
            Each upload starts a transcription job.
          </p>
        </div>
        <UploadSermon />
      </section>

      <section className="surface-card">
        <div className="border-b border-[color:var(--line)] px-6 py-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-sm font-semibold">Recent sermons</p>
              {!loading && sermons.length > 0 ? (
                <span className="text-xs text-[color:var(--muted)]">
                  Showing {sermons.length}
                  {hasNextPage ? "+" : ""}
                </span>
              ) : null}
            </div>
            {fetching ? (
              <span className="inline-flex items-center gap-2 text-xs text-[color:var(--muted)]">
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--line)] border-t-[color:var(--accent)]" />
                {loading ? "Loading sermons..." : "Refreshing..."}
              </span>
            ) : null}
          </div>
          <div className="mt-4 flex flex-wrap items-end gap-3">
            <label className="flex min-w-[220px] flex-1 flex-col gap-2 text-xs uppercase tracking-wide text-[color:var(--muted)]">
              Search
              <input
                type="text"
                value={searchText}
                onChange={(event) => setSearchText(event.target.value)}
                placeholder="Title, preacher, tags..."
                className="rounded-xl border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2 text-sm normal-case text-[color:var(--ink)] placeholder:text-[color:var(--muted)] focus:border-[color:var(--accent)] focus:outline-none"
                disabled={loading}
              />
            </label>
            <label className="flex min-w-[160px] flex-col gap-2 text-xs uppercase tracking-wide text-[color:var(--muted)]">
              Status
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="rounded-xl border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2 text-sm normal-case text-[color:var(--ink)] focus:border-[color:var(--accent)] focus:outline-none"
                disabled={loading}
              >
                <option value="all">All statuses</option>
                {statusOptions.map((status) => (
                  <option key={status} value={status}>
                    {formatStatus(status)}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex min-w-[160px] flex-col gap-2 text-xs uppercase tracking-wide text-[color:var(--muted)]">
              Tag
              <input
                value={tagFilter}
                onChange={(event) => setTagFilter(event.target.value)}
                className="rounded-xl border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2 text-sm normal-case text-[color:var(--ink)] focus:border-[color:var(--accent)] focus:outline-none disabled:opacity-60"
                disabled={loading}
                placeholder="All tags"
                list="tag-options"
              />
              <datalist id="tag-options">
                {tagOptions.map((tag) => (
                  <option key={tag} value={tag} />
                ))}
              </datalist>
            </label>
            <button
              type="button"
              onClick={clearFilters}
              className="btn btn-outline px-3 py-2 text-xs disabled:opacity-50"
              disabled={!hasFilters || loading}
            >
              Clear filters
            </button>
          </div>
        </div>
        <div className="divide-y divide-[color:var(--line)]">
          {loading
            ? Array.from({ length: LOADING_ROWS }).map((_, index) => (
                <div key={`loading-${index}`} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-2">
                      <div className="h-3 w-40 animate-pulse rounded bg-[color:var(--bg-elevated)]" />
                      <div className="h-2 w-32 animate-pulse rounded bg-[color:var(--bg-elevated)]" />
                    </div>
                    <div className="h-2 w-10 animate-pulse rounded bg-[color:var(--bg-elevated)]" />
                  </div>
                </div>
              ))
            : null}
          {error ? (
            <p className="px-6 py-4 text-sm text-[#a33a2b]">{error}</p>
          ) : null}
          {!loading && sermons.length === 0 && !hasFilters ? (
            <p className="px-6 py-4 text-sm text-[color:var(--muted)]">
              No sermons yet.
            </p>
          ) : null}
          {!loading && sermons.length === 0 && hasFilters ? (
            <p className="px-6 py-4 text-sm text-[color:var(--muted)]">
              No sermons match the current filters.
            </p>
          ) : null}
          {!loading ? sermons.map((sermon) => {
            const metaParts = [];
            if (sermon.preacher) metaParts.push(`Preacher: ${sermon.preacher}`);
            if (sermon.series) metaParts.push(`Series: ${sermon.series}`);
            if (sermon.sermon_date) metaParts.push(`Date: ${sermon.sermon_date}`);
            const tags = Array.isArray(sermon.tags) ? sermon.tags : [];
            const metaLine = metaParts.join(" | ");
            return (
              <Link
                key={sermon.id}
                href={`/app/sermons/${sermon.id}`}
                className="block px-6 py-4 transition hover:bg-[color:var(--surface-soft)]"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-semibold">
                        {sermon.title || `Sermon #${sermon.id}`}
                      </p>
                      <span className="rounded-full border border-[color:var(--line)] px-2 py-0.5 text-[10px] uppercase tracking-wide text-[color:var(--muted)]">
                        {formatStatus(sermon.status)}
                      </span>
                    </div>
                    {metaLine ? (
                      <p className="mt-1 text-xs text-[color:var(--muted)]">
                        {metaLine}
                      </p>
                    ) : null}
                    <p className="text-xs text-[color:var(--muted)]">
                      {typeof sermon.progress === "number"
                        ? `Progress ${Math.min(100, Math.max(0, sermon.progress))}%`
                        : "No progress yet"}
                    </p>
                    {sermon.error_message ? (
                      <p className="mt-1 text-xs text-[#a33a2b]">
                        {sermon.error_message}
                      </p>
                    ) : null}
                    {tags.length > 0 ? (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {tags.map((tag, index) => (
                          <span
                            key={`${sermon.id}-tag-${index}`}
                            className="rounded-full border border-transparent bg-[color:var(--accent-soft)] px-2 py-0.5 text-[10px] uppercase tracking-wide text-[#7a3826]"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    ) : null}
                    {typeof sermon.progress === "number" ? (
                      <div className="mt-2 h-1 w-40 rounded-full bg-[color:var(--bg-elevated)]">
                        <div
                          className="h-1 rounded-full bg-[color:var(--accent)]"
                          style={{
                            width: `${Math.min(100, Math.max(0, sermon.progress))}%`
                          }}
                        />
                      </div>
                    ) : null}
                  </div>
                  <span className="text-xs text-[color:var(--muted)]">View</span>
                </div>
              </Link>
            );
          }) : null}
          {hasNextPage ? (
            <div className="px-6 py-4">
              <button
                type="button"
                onClick={() => sermonsQuery.fetchNextPage()}
                disabled={loadingMore}
                className="btn btn-outline disabled:opacity-50"
              >
                {loadingMore ? "Loading more..." : "Load more"}
              </button>
            </div>
          ) : null}
        </div>
      </section>
    </main>
  );
}
