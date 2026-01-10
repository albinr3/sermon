"use client";

export default function SuggestedClipsPanel({
  useLlmSuggestions,
  onToggleUseLlm,
  llmMethod,
  onSelectLlmMethod,
  llmProvider,
  onSelectLlmProvider,
  onSuggest,
  onDeleteSuggestions,
  onToggleTokenStats,
  tokenStats,
  tokenStatsOpen,
  tokenStatsLoading,
  tokenStatsError,
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
  const fullContextStats = tokenStats?.methods?.["full-context"] || null;
  const formatCost = (value) =>
    typeof value === "number" && Number.isFinite(value)
      ? value.toFixed(6)
      : "0.000000";

  return (
    <section className="surface-card">
      <div className="border-b border-[color:var(--line)] px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold">Suggested Clips</p>
            <p className="text-xs text-[color:var(--muted)]">Auto-selected ranges.</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-xs text-[color:var(--muted)]">
              <input
                type="checkbox"
                checked={useLlmSuggestions}
                onChange={(event) => onToggleUseLlm(event.target.checked)}
                disabled={suggesting}
                className="h-4 w-4 rounded border-[color:var(--line)] bg-[color:var(--surface)] text-[color:var(--accent)]"
              />
              Usar IA para sugerir clips
            </label>
            {useLlmSuggestions ? (
              <div className="flex flex-col gap-1 text-xs text-[color:var(--muted)]">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="llm-provider"
                    value="deepseek"
                    checked={llmProvider === "deepseek"}
                    onChange={() => onSelectLlmProvider("deepseek")}
                    disabled={suggesting}
                    className="h-4 w-4 border-[color:var(--line)] text-[color:var(--accent)]"
                  />
                  DeepSeek
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="llm-provider"
                    value="openai"
                    checked={llmProvider === "openai"}
                    onChange={() => onSelectLlmProvider("openai")}
                    disabled={suggesting}
                    className="h-4 w-4 border-[color:var(--line)] text-[color:var(--accent)]"
                  />
                  OpenAI GPT-5 mini
                </label>
              </div>
            ) : null}
            {useLlmSuggestions ? (
              <div className="flex flex-col gap-1 text-xs text-[color:var(--muted)]">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="llm-method"
                    value="full-context"
                    checked={llmMethod === "full-context"}
                    onChange={() => onSelectLlmMethod("full-context")}
                    disabled={suggesting}
                    className="h-4 w-4 border-[color:var(--line)] text-[color:var(--accent)]"
                  />
                  Full Context - ~60K tokens, $0.012, 120s - Maxima calidad
                </label>
              </div>
            ) : null}
            {useLlmSuggestions && llmMethod === "full-context" ? (
              <div className="text-xs text-[#7a4a12]">
                Warning: ~60K tokens, hasta $0.012 por sermon.
              </div>
            ) : null}
            <button
              type="button"
              onClick={onSuggest}
              disabled={suggesting}
              className="btn btn-primary text-sm disabled:opacity-50"
            >
              {suggesting ? "Suggesting..." : "Generate suggestions"}
            </button>
            <button
              type="button"
              onClick={onDeleteSuggestions}
              disabled={suggesting || suggestionsLocked}
              className="btn btn-outline text-sm disabled:opacity-50"
            >
              Delete suggestions
            </button>
            <button
              type="button"
              onClick={onToggleTokenStats}
              disabled={tokenStatsLoading}
              className="btn btn-outline text-sm disabled:opacity-50"
            >
              {tokenStatsOpen ? "Hide token stats" : "View token stats"}
            </button>
            {suggesting ? (
              <div className="flex items-center gap-2 text-xs text-[color:var(--muted)]">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-[color:var(--line)] border-t-[color:var(--accent)]" />
                Generando sugerencias...
              </div>
            ) : null}
          </div>
        </div>
        {showProgress ? (
          <div className="mt-4">
            <div className="flex items-center justify-between text-[10px] uppercase tracking-wide text-[color:var(--muted)]">
              <span>{progressLabel}</span>
              <span>{progressDisplay}%</span>
            </div>
            <div className="mt-2 h-2 w-full rounded-full bg-[color:var(--bg-elevated)]">
              <div
                className="h-2 rounded-full bg-[color:var(--accent)] transition-all duration-500"
                style={{ width: `${progressValue}%` }}
              />
            </div>
          </div>
        ) : null}
        {tokenStatsOpen ? (
          <div className="mt-4 rounded-xl border border-[color:var(--line)] bg-[color:var(--surface-soft)] p-4 text-xs text-[color:var(--muted)]">
            {tokenStatsLoading ? (
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--line)] border-t-[color:var(--accent)]" />
                Loading token stats...
              </div>
            ) : tokenStatsError ? (
              <p className="text-[#a33a2b]">{tokenStatsError}</p>
            ) : fullContextStats ? (
              <div className="space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span>
                    Full Context: {fullContextStats.total_tokens || 0} tokens ú
                    output {fullContextStats.output_tokens || 0} ú cache hit{" "}
                    {fullContextStats.cache_hit_tokens || 0} ú miss{" "}
                    {fullContextStats.cache_miss_tokens || 0}
                  </span>
                  <span>${formatCost(fullContextStats.estimated_cost_usd)} USD</span>
                </div>
              </div>
            ) : (
              <p>No token stats available yet.</p>
            )}
          </div>
        ) : null}
      </div>
      <div className="divide-y divide-[color:var(--line)] px-6 py-4">
        {suggestionsLoading ? (
          <div className="flex items-center gap-3 text-sm text-[color:var(--muted)]">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-[color:var(--line)] border-t-[color:var(--accent)]" />
            Loading suggestions...
          </div>
        ) : suggestionsError ? (
          <p className="text-sm text-[#a33a2b]">{suggestionsError}</p>
        ) : suggestionsLocked ? (
          <div className="flex items-center gap-3 text-sm text-[color:var(--muted)]">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-[color:var(--line)] border-t-[color:var(--accent)]" />
            Preparing previews...
          </div>
        ) : suggestions.length === 0 ? (
          <p className="text-sm text-[color:var(--muted)]">No suggestions yet.</p>
        ) : (
          suggestions.map((clip) => {
            const isBusy = Boolean(actionLoading[clip.id]);
            const trimLabel = formatTrimSuggestion(clip.llm_trim);
            const methodLabel = clip.llm_method ? `Method ${clip.llm_method}` : "";
            const tokensLabel =
              clip.llm_total_tokens !== null && clip.llm_total_tokens !== undefined
                ? `${clip.llm_total_tokens} tokens`
                : "";
            const outputTokens =
              clip.llm_output_tokens ?? clip.llm_completion_tokens;
            const outputLabel =
              outputTokens !== null && outputTokens !== undefined
                ? `output ${outputTokens}`
                : "";
            const cacheHitLabel =
              clip.llm_cache_hit_tokens !== null &&
              clip.llm_cache_hit_tokens !== undefined
                ? `hit ${clip.llm_cache_hit_tokens}`
                : "";
            const cacheMissLabel =
              clip.llm_cache_miss_tokens !== null &&
              clip.llm_cache_miss_tokens !== undefined
                ? `miss ${clip.llm_cache_miss_tokens}`
                : "";
            const cacheLabel =
              cacheHitLabel || cacheMissLabel
                ? `cache ${[cacheHitLabel, cacheMissLabel].filter(Boolean).join(", ")}`
                : "";
            const tokenDetails = [outputLabel, cacheLabel].filter(Boolean).join(" · ");
            const costLabel =
              typeof clip.llm_estimated_cost === "number" &&
              Number.isFinite(clip.llm_estimated_cost)
                ? `$${clip.llm_estimated_cost.toFixed(6)} USD`
                : "";
            return (
              <div key={clip.id} className="flex flex-col gap-3 py-4">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full border border-[color:var(--line)] px-2 py-0.5 text-xs text-[color:var(--muted)]">
                        Start {formatTimestamp(clip.start_ms)}
                      </span>
                      <span className="rounded-full border border-[color:var(--line)] px-2 py-0.5 text-xs text-[color:var(--muted)]">
                        End {formatTimestamp(clip.end_ms)}
                      </span>
                      <span className="text-xs text-[color:var(--muted)]">
                        {Math.round((clip.end_ms - clip.start_ms) / 1000)}s
                      </span>
                    </div>
                    <p className="text-xs text-[color:var(--muted)]">
                      Score {clip.score?.toFixed(2) ?? "0.00"} -{" "}
                      {formatClipStatus(clip.status)}
                      {clip.use_llm ? (
                        <span className="ml-2 inline-flex rounded-full border border-[color:var(--accent-2)] px-2 py-0.5 text-[10px] uppercase tracking-wide text-[color:var(--accent-2-strong)]">
                          IA
                        </span>
                      ) : null}
                    </p>
                    {clip.rationale ? (
                      <p className="mt-2 text-xs text-[color:var(--muted)]">
                        {clip.rationale}
                      </p>
                    ) : null}
                    {methodLabel || tokensLabel ? (
                      <p className="mt-2 text-xs text-[color:var(--muted)]">
                        {methodLabel}
                        {methodLabel && tokensLabel ? " - " : ""}
                        {tokensLabel}
                        {tokenDetails ? ` · ${tokenDetails}` : ""}
                        {costLabel ? ` (${costLabel})` : ""}
                      </p>
                    ) : null}
                    {trimLabel ? (
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-[color:var(--muted)]">
                        <span>{trimLabel}</span>
                        {clip.trim_applied ? (
                          <span className="rounded-full border border-[color:var(--accent-2)] px-2 py-0.5 text-[10px] uppercase tracking-wide text-[color:var(--accent-2-strong)]">
                            Recorte aplicado
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={() => onApplyTrim(clip)}
                            disabled={isBusy}
                            className="btn btn-secondary px-2 py-0.5 text-[10px] uppercase tracking-wide disabled:opacity-50"
                          >
                            Aplicar
                          </button>
                        )}
                      </div>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {isBusy ? (
                      <span className="inline-flex items-center gap-2 text-xs text-[color:var(--muted)]">
                        <span className="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--line)] border-t-[color:var(--accent)]" />
                        Working...
                      </span>
                    ) : null}
                    <button
                      type="button"
                      onClick={() => onRender(clip, "preview")}
                      disabled={isBusy}
                      className="btn btn-outline px-3 py-1 text-xs disabled:opacity-50"
                    >
                      Preview
                    </button>
                    <button
                      type="button"
                      onClick={() => onRender(clip, "final")}
                      disabled={isBusy}
                      className="btn btn-outline px-3 py-1 text-xs disabled:opacity-50"
                    >
                      Render Final
                    </button>
                    <button
                      type="button"
                      onClick={() => onAccept(clip)}
                      disabled={isBusy}
                      className="btn btn-primary px-3 py-1 text-xs disabled:opacity-50"
                    >
                      Accept
                    </button>
                    <button
                      type="button"
                      onClick={() => onReject(clip)}
                      disabled={isBusy}
                      className="btn btn-danger px-3 py-1 text-xs disabled:opacity-50"
                    >
                      Reject
                    </button>
                    <button
                      type="button"
                      onClick={() => onEdit(clip)}
                      className="btn btn-outline px-3 py-1 text-xs"
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
