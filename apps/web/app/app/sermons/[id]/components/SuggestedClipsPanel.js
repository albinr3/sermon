"use client";

export default function SuggestedClipsPanel({
  useLlmSuggestions,
  onToggleUseLlm,
  onSuggest,
  suggesting,
  suggestionsLoading,
  suggestionsError,
  suggestionsPending,
  suggestionsProgress,
  suggestionsProgressLabel,
  suggestionsShowProgress,
  suggestionsLocked,
  suggestions,
  actionLoading,
  onApplyTrim,
  onRender,
  onAccept,
  onReject,
  onEdit,
  formatTimestamp,
  formatClipStatus,
  formatTrimSuggestion
}) {
  const showProgress = suggestionsShowProgress || suggestionsPending;
  const progressValue =
    typeof suggestionsProgress === "number"
      ? Math.max(6, Math.min(100, suggestionsProgress))
      : 6;
  const progressDisplay = Math.round(progressValue);
  const progressLabel = suggestionsProgressLabel || "Estimated progress";

  return (
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
                onChange={(event) => onToggleUseLlm(event.target.checked)}
                disabled={suggesting}
                className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-emerald-400"
              />
              Usar IA para sugerir clips
            </label>
            <button
              type="button"
              onClick={onSuggest}
              disabled={suggesting}
              className="rounded-full border border-slate-800 px-4 py-2 text-sm text-slate-100 hover:border-slate-700 disabled:opacity-50"
            >
              {suggesting ? "Suggesting..." : "Generate suggestions"}
            </button>
            {suggesting ? (
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-700 border-t-emerald-500" />
                Generando sugerencias...
              </div>
            ) : null}
          </div>
        </div>
        {showProgress ? (
          <div className="mt-4">
            <div className="flex items-center justify-between text-[10px] uppercase tracking-wide text-slate-500">
              <span>{progressLabel}</span>
              <span>{progressDisplay}%</span>
            </div>
            <div className="mt-2 h-2 w-full rounded-full bg-slate-900">
              <div
                className="h-2 rounded-full bg-emerald-500/70 transition-all duration-500"
                style={{ width: `${progressValue}%` }}
              />
            </div>
          </div>
        ) : null}
      </div>
      <div className="divide-y divide-slate-900 px-6 py-4">
        {suggestionsLoading ? (
          <div className="flex items-center gap-3 text-sm text-slate-400">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-700 border-t-emerald-500" />
            Loading suggestions...
          </div>
        ) : suggestionsError ? (
          <p className="text-sm text-red-400">{suggestionsError}</p>
        ) : suggestionsLocked ? (
          <div className="flex items-center gap-3 text-sm text-slate-400">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-700 border-t-emerald-500" />
            Preparing previews...
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
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full border border-slate-800 px-2 py-0.5 text-xs text-slate-400">
                        Start {formatTimestamp(clip.start_ms)}
                      </span>
                      <span className="rounded-full border border-slate-800 px-2 py-0.5 text-xs text-slate-400">
                        End {formatTimestamp(clip.end_ms)}
                      </span>
                      <span className="text-xs text-slate-500">
                        {Math.round((clip.end_ms - clip.start_ms) / 1000)}s
                      </span>
                    </div>
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
                            onClick={() => onApplyTrim(clip)}
                            disabled={isBusy}
                            className="rounded-full border border-emerald-500/50 px-2 py-0.5 text-[10px] uppercase tracking-wide text-emerald-200 hover:border-emerald-400 disabled:opacity-50"
                          >
                            Aplicar
                          </button>
                        )}
                      </div>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {isBusy ? (
                      <span className="inline-flex items-center gap-2 text-xs text-slate-400">
                        <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-700 border-t-emerald-500" />
                        Working...
                      </span>
                    ) : null}
                    <button
                      type="button"
                      onClick={() => onRender(clip, "preview")}
                      disabled={isBusy}
                      className="rounded-full border border-slate-800 px-3 py-1 text-xs text-slate-100 hover:border-slate-700 disabled:opacity-50"
                    >
                      Preview
                    </button>
                    <button
                      type="button"
                      onClick={() => onRender(clip, "final")}
                      disabled={isBusy}
                      className="rounded-full border border-slate-800 px-3 py-1 text-xs text-slate-100 hover:border-slate-700 disabled:opacity-50"
                    >
                      Render Final
                    </button>
                    <button
                      type="button"
                      onClick={() => onAccept(clip)}
                      disabled={isBusy}
                      className="rounded-full border border-emerald-500/50 px-3 py-1 text-xs text-emerald-200 hover:border-emerald-400 disabled:opacity-50"
                    >
                      Accept
                    </button>
                    <button
                      type="button"
                      onClick={() => onReject(clip)}
                      disabled={isBusy}
                      className="rounded-full border border-rose-500/50 px-3 py-1 text-xs text-rose-200 hover:border-rose-400 disabled:opacity-50"
                    >
                      Reject
                    </button>
                    <button
                      type="button"
                      onClick={() => onEdit(clip)}
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
  );
}
