import { z } from "zod";

export const sermonStatusSchema = z.enum([
  "pending",
  "uploaded",
  "processing",
  "transcribed",
  "suggested",
  "embedded",
  "error",
  "completed",
  "failed"
]);

export const clipStatusSchema = z.enum(["pending", "processing", "done", "error"]);
export const clipSourceSchema = z.enum(["manual", "auto"]);
export const clipReframeModeSchema = z.enum(["center", "face"]);
export const clipRenderTypeSchema = z.enum(["preview", "final"]);

export const sermonSchema = z.object({
  id: z.number(),
  title: z.string().nullable(),
  description: z.string().nullable().optional(),
  preacher: z.string().nullable().optional(),
  series: z.string().nullable().optional(),
  sermon_date: z.string().nullable().optional(),
  tags: z.array(z.string()).nullable().optional(),
  source_url: z.string().nullable(),
  source_download_url: z.string().nullable().optional(),
  progress: z.number(),
  status: sermonStatusSchema,
  error_message: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  deleted_at: z.string().nullable().optional()
});

export const sermonListSchema = z.array(sermonSchema);

export const clipSchema = z.object({
  id: z.number(),
  sermon_id: z.number(),
  start_ms: z.number(),
  end_ms: z.number(),
  output_url: z.string().nullable(),
  download_url: z.string().nullable().optional(),
  status: clipStatusSchema,
  source: clipSourceSchema,
  score: z.number().nullable().optional(),
  rationale: z.string().nullable().optional(),
  use_llm: z.boolean(),
  llm_prompt_tokens: z.number().nullable().optional(),
  llm_completion_tokens: z.number().nullable().optional(),
  llm_total_tokens: z.number().nullable().optional(),
  llm_estimated_cost: z.number().nullable().optional(),
  llm_output_tokens: z.number().nullable().optional(),
  llm_cache_hit_tokens: z.number().nullable().optional(),
  llm_cache_miss_tokens: z.number().nullable().optional(),
  llm_method: z.string().nullable().optional(),
  llm_trim: z.record(z.any()).nullable().optional(),
  llm_trim_confidence: z.number().nullable().optional(),
  trim_applied: z.boolean(),
  template_id: z.string().nullable().optional(),
  reframe_mode: clipReframeModeSchema,
  render_type: clipRenderTypeSchema,
  created_at: z.string(),
  updated_at: z.string(),
  deleted_at: z.string().nullable().optional()
});

export const clipListSchema = z.array(clipSchema);

export const transcriptSegmentSchema = z.object({
  id: z.number(),
  sermon_id: z.number(),
  start_ms: z.number(),
  end_ms: z.number(),
  text: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  deleted_at: z.string().nullable().optional()
});

export const transcriptSegmentListSchema = z.array(transcriptSegmentSchema);

export const createSermonResponseSchema = z.object({
  sermon: sermonSchema,
  upload_url: z.string(),
  object_key: z.string()
});

export const uploadCompleteResponseSchema = z.object({
  sermon: sermonSchema
});

export const embedResponseSchema = z.object({
  sermon_id: z.number(),
  status: z.string()
});

export const suggestClipsResponseSchema = z.object({
  sermon_id: z.number(),
  status: z.string()
});

export const clipSuggestionsResponseSchema = z.object({
  sermon_id: z.number(),
  clips: z.array(clipSchema)
});

export const clipAcceptResponseSchema = z.object({
  suggestion_id: z.number(),
  clip: clipSchema
});

export const clipFeedbackSchema = z.object({
  id: z.number(),
  clip_id: z.number(),
  accepted: z.boolean(),
  user_id: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  deleted_at: z.string().nullable().optional()
});

export const clipRenderResponseSchema = z.object({
  clip_id: z.number(),
  status: z.string(),
  render_type: clipRenderTypeSchema
});

export const searchResultSchema = z.object({
  segment_id: z.number(),
  text: z.string(),
  start_ms: z.number(),
  end_ms: z.number()
});

export const searchResponseSchema = z.object({
  sermon_id: z.number(),
  query: z.string(),
  results: z.array(searchResultSchema)
});
