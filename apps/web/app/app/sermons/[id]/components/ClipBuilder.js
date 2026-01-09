"use client";

import { useEffect, useRef, useState } from "react";

const MIN_DURATION_MS = 10_000;
const MAX_DURATION_MS = 120_000;

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

export default function ClipBuilder({
  title,
  subtitle,
  segments,
  mediaUrl,
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
  const audioRef = useRef(null);

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

  const selectionPhase =
    selection.startIndex === null
      ? "start"
      : selection.endIndex === null
      ? "end"
      : "ready";

  const selectionHint =
    selectionPhase === "start"
      ? "Step 1: Select a start segment."
      : selectionPhase === "end"
      ? "Step 2: Select an end segment."
      : "Range ready. Click a segment to start over.";

  const selectionStartSec =
    selectionStartMs !== null ? Math.max(0, selectionStartMs / 1000) : null;
  const selectionEndSec =
    selectionEndMs !== null ? Math.max(0, selectionEndMs / 1000) : null;
  const previewReady =
    Boolean(mediaUrl) &&
    selectionReady &&
    selectionStartSec !== null &&
    selectionEndSec !== null;
  const previewSrc = previewReady
    ? `${mediaUrl}#t=${selectionStartSec},${selectionEndSec}`
    : null;

  const handlePreview = () => {
    if (!audioRef.current || !previewReady) return;
    audioRef.current.currentTime = selectionStartSec;
    audioRef.current.play();
  };

  const handleAudioTimeUpdate = () => {
    if (!audioRef.current || selectionEndSec === null) return;
    if (audioRef.current.currentTime >= selectionEndSec) {
      audioRef.current.pause();
    }
  };

  useEffect(() => {
    if (!audioRef.current) return;
    audioRef.current.pause();
    audioRef.current.currentTime = 0;
  }, [selectionStartMs, selectionEndMs]);

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
          <>
            <div className="rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-2 text-xs text-slate-400">
              {selectionHint}
            </div>
            <div className="space-y-3">
              {segments.map((segment, index) => {
                const isSelected =
                  selectionRange &&
                  index >= selectionRange[0] &&
                  index <= selectionRange[1];
                const isStart = selection.startIndex === index;
                const isEnd = selection.endIndex === index;
                const selectionClass = isStart
                  ? "border-emerald-400/80 bg-emerald-500/10"
                  : isEnd
                  ? "border-amber-400/80 bg-amber-500/10"
                  : isSelected
                  ? "border-emerald-500/50 bg-emerald-500/5"
                  : "border-slate-800 hover:border-slate-700";

                return (
                  <button
                    key={segment.id}
                    type="button"
                    onClick={() => handleSegmentClick(index)}
                    className={`w-full rounded-lg border p-3 text-left transition ${selectionClass}`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                        <span className="rounded-full border border-slate-800 px-2 py-0.5">
                          Start {formatTimestamp(segment.start_ms)}
                        </span>
                        <span className="rounded-full border border-slate-800 px-2 py-0.5">
                          End {formatTimestamp(segment.end_ms)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] uppercase tracking-wide">
                        {isStart ? (
                          <span className="rounded-full border border-emerald-500/60 px-2 py-0.5 text-emerald-200">
                            Start
                          </span>
                        ) : null}
                        {isEnd ? (
                          <span className="rounded-full border border-amber-500/60 px-2 py-0.5 text-amber-200">
                            End
                          </span>
                        ) : null}
                      </div>
                    </div>
                    <p className="mt-2 text-sm text-slate-200">{segment.text}</p>
                  </button>
                );
              })}
            </div>
          </>
        )}
      </div>
      <div className="border-t border-slate-800 px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="text-sm text-slate-400">
            {selectionReady ? (
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-slate-800 px-2 py-0.5 text-xs text-slate-400">
                  Start {formatTimestamp(selectionStartMs)}
                </span>
                <span className="rounded-full border border-slate-800 px-2 py-0.5 text-xs text-slate-400">
                  End {formatTimestamp(selectionEndMs)}
                </span>
                <span className="text-xs text-slate-500">
                  {Math.round(selectionDurationMs / 1000)}s total
                </span>
              </div>
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
        {mediaUrl ? (
          <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/60 p-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-slate-400">Audio preview</p>
              {previewReady ? (
                <button
                  type="button"
                  onClick={handlePreview}
                  className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-200 hover:border-slate-500"
                >
                  Play selection
                </button>
              ) : null}
            </div>
            {previewReady ? (
              <div className="mt-3">
                <audio
                  key={previewSrc}
                  ref={audioRef}
                  controls
                  preload="metadata"
                  onTimeUpdate={handleAudioTimeUpdate}
                  className="w-full"
                  src={previewSrc}
                />
              </div>
            ) : (
              <p className="mt-2 text-xs text-slate-500">
                Select a range to enable the audio preview.
              </p>
            )}
          </div>
        ) : (
          <p className="mt-4 text-xs text-slate-500">
            Audio preview will appear once the source video is available.
          </p>
        )}
        {clipError ? <p className="mt-2 text-sm text-red-400">{clipError}</p> : null}
      </div>
    </section>
  );
}
