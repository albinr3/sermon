"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import {
  createSermon,
  markUploadComplete,
  uploadToPresignedUrl
} from "../../lib/api";

const uploadSchema = z.object({
  file: z
    .instanceof(File, { message: "Select a video file." })
    .refine((file) => file.size > 0, { message: "File is empty." })
    .refine((file) => file.type.startsWith("video/"), {
      message: "File must be a video."
    })
});

export default function UploadSermon({ onUploaded }) {
  const inputRef = useRef(null);
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    setValue,
    reset,
    formState: { errors }
  } = useForm({
    resolver: zodResolver(uploadSchema)
  });
  const { ref: fileRef, ...fileField } = register("file");

  const uploadMutation = useMutation({
    mutationFn: async ({ file }) => {
      const payload = await createSermon(file.name);
      await uploadToPresignedUrl(payload.upload_url, file);
      await markUploadComplete(payload.sermon.id);
      return payload;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sermons"] });
      onUploaded?.();
      reset();
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  });

  const onSubmit = async (values) => {
    await uploadMutation.mutateAsync(values);
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file || uploadMutation.isPending) return;
    setValue("file", file, { shouldValidate: true });
    handleSubmit(onSubmit)();
  };

  const errorMessage =
    errors.file?.message || uploadMutation.error?.message || "";

  return (
    <div className="flex flex-col gap-2">
      <label className="inline-flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-100 hover:border-slate-700">
        <input
          {...fileField}
          ref={(node) => {
            fileRef(node);
            inputRef.current = node;
          }}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={handleFileChange}
          disabled={uploadMutation.isPending}
        />
        <span className="inline-flex items-center gap-2">
          {uploadMutation.isPending ? (
            <>
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-700 border-t-emerald-400" />
              Uploading...
            </>
          ) : (
            "Upload sermon"
          )}
        </span>
      </label>
      {errorMessage ? (
        <p className="text-sm text-red-400">{errorMessage}</p>
      ) : null}
    </div>
  );
}
