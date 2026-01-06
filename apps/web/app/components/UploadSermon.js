"use client";

import { useRef, useState } from "react";

import {
  createSermon,
  markUploadComplete,
  uploadToPresignedUrl
} from "../../lib/api";

export default function UploadSermon({ onUploaded }) {
  const inputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError("");

    try {
      const payload = await createSermon(file.name);
      await uploadToPresignedUrl(payload.upload_url, file);
      await markUploadComplete(payload.sermon.id);
      onUploaded?.();
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <label className="inline-flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-100 hover:border-slate-700">
        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={handleUpload}
          disabled={loading}
        />
        <span>{loading ? "Uploading..." : "Upload sermon"}</span>
      </label>
      {error ? <p className="text-sm text-red-400">{error}</p> : null}
    </div>
  );
}
