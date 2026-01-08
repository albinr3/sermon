import { ZodError } from "zod";

import {
  clipAcceptResponseSchema,
  clipFeedbackSchema,
  clipListSchema,
  clipRenderResponseSchema,
  clipSchema,
  clipSuggestionsResponseSchema,
  createSermonResponseSchema,
  embedResponseSchema,
  searchResponseSchema,
  sermonListSchema,
  sermonSchema,
  suggestClipsResponseSchema,
  transcriptSegmentListSchema,
  uploadCompleteResponseSchema
} from "./schemas";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch(path, options = {}, schema) {
  const url = `${API_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `API error ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  const data = await response.json();
  if (!schema) {
    return data;
  }
  try {
    return schema.parse(data);
  } catch (err) {
    if (err instanceof ZodError) {
      throw new Error("Invalid response from server");
    }
    throw err;
  }
}

export async function listSermons() {
  return apiFetch("/sermons/", {}, sermonListSchema);
}

export async function createSermon(filename) {
  return apiFetch("/sermons/", {
    method: "POST",
    body: JSON.stringify({ filename })
  }, createSermonResponseSchema);
}

export async function markUploadComplete(id) {
  return apiFetch(`/sermons/${id}/upload-complete`, {
    method: "POST"
  }, uploadCompleteResponseSchema);
}

export async function getSermon(id) {
  return apiFetch(`/sermons/${id}`, {}, sermonSchema);
}

export async function getTranscriptSegments(id) {
  return apiFetch(`/sermons/${id}/segments`, {}, transcriptSegmentListSchema);
}

export async function listClips() {
  return apiFetch("/clips/", {}, clipListSchema);
}

export async function getClip(id) {
  return apiFetch(`/clips/${id}`, {}, clipSchema);
}

export async function createClip({ sermon_id, start_ms, end_ms, render_type }) {
  return apiFetch("/clips/", {
    method: "POST",
    body: JSON.stringify({ sermon_id, start_ms, end_ms, render_type })
  }, clipSchema);
}

export async function suggestClips(id, useLlm) {
  const params = new URLSearchParams();
  if (typeof useLlm === "boolean") {
    params.set("use_llm", String(useLlm));
  }
  const query = params.toString();
  return apiFetch(`/sermons/${id}/suggest${query ? `?${query}` : ""}`, {
    method: "POST"
  }, suggestClipsResponseSchema);
}

export async function generateEmbeddings(id) {
  return apiFetch(`/sermons/${id}/embed`, {
    method: "POST"
  }, embedResponseSchema);
}

export async function listSuggestions(id) {
  return apiFetch(`/sermons/${id}/suggestions`, {}, clipSuggestionsResponseSchema);
}

export async function acceptSuggestion(clipId) {
  return apiFetch(`/clips/${clipId}/accept`, {
    method: "POST"
  }, clipAcceptResponseSchema);
}

export async function recordClipFeedback(clipId, { accepted, user_id } = {}) {
  return apiFetch(`/clips/${clipId}/feedback`, {
    method: "POST",
    body: JSON.stringify({ accepted, user_id })
  }, clipFeedbackSchema);
}

export async function applyTrimSuggestion(clipId) {
  return apiFetch(`/clips/${clipId}/apply-trim`, {
    method: "POST"
  }, clipSchema);
}

export async function renderClip(clipId, renderType) {
  const params = new URLSearchParams({ type: renderType });
  return apiFetch(`/clips/${clipId}/render?${params.toString()}`, {
    method: "POST"
  }, clipRenderResponseSchema);
}

export async function searchSermon(id, query, k = 10) {
  const params = new URLSearchParams({ q: query, k: String(k) });
  return apiFetch(
    `/sermons/${id}/search?${params.toString()}`,
    {},
    searchResponseSchema
  );
}

export async function uploadToPresignedUrl(uploadUrl, file) {
  const response = await fetch(uploadUrl, {
    method: "PUT",
    headers: {
      "Content-Type": file.type || "application/octet-stream"
    },
    body: file
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Upload failed ${response.status}`);
  }
}
