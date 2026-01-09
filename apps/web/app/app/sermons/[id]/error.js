"use client";

export default function SermonError({ error, reset }) {
  const message = error?.message ? String(error.message).slice(0, 200) : "Unknown error";
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-4 px-6 py-16">
      <span className="pill w-fit">Sermon</span>
      <h1 className="text-2xl">
        Sermon details failed to load
      </h1>
      <p className="text-sm text-[color:var(--muted)]">{message}</p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => reset()}
          className="btn btn-primary text-sm"
        >
          Try again
        </button>
        <a
          href="/app"
          className="btn btn-outline text-sm"
        >
          Back home
        </a>
      </div>
    </main>
  );
}
