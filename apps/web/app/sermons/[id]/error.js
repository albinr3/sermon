"use client";

export default function SermonError({ error, reset }) {
  const message = error?.message ? String(error.message).slice(0, 200) : "Unknown error";
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-4 px-6 py-16">
      <h1 className="text-2xl font-semibold text-slate-100">
        Sermon details failed to load
      </h1>
      <p className="text-sm text-slate-400">{message}</p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => reset()}
          className="rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-100 hover:border-slate-500"
        >
          Try again
        </button>
        <a
          href="/"
          className="rounded-full border border-slate-800 px-4 py-2 text-sm text-slate-300 hover:border-slate-700"
        >
          Back home
        </a>
      </div>
    </main>
  );
}
