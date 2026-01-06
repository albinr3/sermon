const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch(path, options = {}) {
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

  return response.json();
}

export async function listSermons() {
  return apiFetch("/sermons");
}

export async function createSermon(filename) {
  return apiFetch("/sermons", {
    method: "POST",
    body: JSON.stringify({ filename })
  });
}

export async function markUploadComplete(id) {
  return apiFetch(`/sermons/${id}/upload-complete`, {
    method: "POST"
  });
}

export async function getSermon(id) {
  return apiFetch(`/sermons/${id}`);
}

export async function getTranscriptSegments(id) {
  return apiFetch(`/sermons/${id}/segments`);
}

export async function listClips() {
  return apiFetch("/clips");
}

export async function createClip({ sermon_id, start_ms, end_ms }) {
  return apiFetch("/clips", {
    method: "POST",
    body: JSON.stringify({ sermon_id, start_ms, end_ms })
  });
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
