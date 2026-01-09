"use client";

export default function Error({ error, reset }) {
  const message = error?.message ? String(error.message).slice(0, 200) : "Unknown error";
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-4 px-6 py-16">
      <span className="pill w-fit">System</span>
      <h1 className="text-2xl">Something went wrong</h1>
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
          href="/"
          className="btn btn-outline text-sm"
        >
          Back home
        </a>
      </div>
    </main>
  );
}
