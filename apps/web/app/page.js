import Link from "next/link";

const FEATURES = [
  {
    title: "Upload once",
    description: "Drop a video, we handle the rest with structured status updates."
  },
  {
    title: "Smart suggestions",
    description: "Generate clip ideas and refine them with a guided editor."
  },
  {
    title: "Ready to share",
    description: "Render previews and finals without leaving the dashboard."
  }
];

const STEPS = [
  {
    title: "1. Upload",
    description: "Send a sermon video and track the job in real time."
  },
  {
    title: "2. Transcribe",
    description: "Segments arrive automatically, ready for search and review."
  },
  {
    title: "3. Clip",
    description: "Choose ranges, apply trims, and render when ready."
  }
];

export default function LandingPage() {
  return (
    <main className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-1/2 top-[-120px] h-80 w-80 -translate-x-1/2 rounded-full bg-emerald-500/10 blur-3xl" />
      <div className="pointer-events-none absolute right-0 top-32 h-64 w-64 rounded-full bg-slate-800/40 blur-3xl" />

      <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-16 px-6 py-12">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-800 bg-slate-900 text-lg font-semibold text-emerald-300">
              S
            </span>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
                SermonClip Studio
              </p>
              <p className="text-sm font-semibold text-slate-200">Clip workflow</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/app"
              className="rounded-full border border-emerald-500/60 px-4 py-2 text-sm text-emerald-200 transition hover:border-emerald-400 hover:text-emerald-100"
            >
              Open app
            </Link>
          </div>
        </header>

        <section className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div className="space-y-6">
            <p className="text-sm uppercase tracking-[0.35em] text-slate-500">
              Sermon clips
            </p>
            <h1 className="text-4xl font-semibold leading-tight text-slate-100 md:text-5xl">
              Turn sermons into shareable moments without the chaos.
            </h1>
            <p className="max-w-xl text-base text-slate-400">
              Organize uploads, track transcription progress, and ship clips from
              one calm workspace. Built for fast iteration and clean handoffs.
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <Link
                href="/app"
                className="rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-slate-900 transition hover:bg-emerald-400"
              >
                Launch dashboard
              </Link>
              <Link
                href="/#workflow"
                className="rounded-full border border-slate-800 px-6 py-3 text-sm text-slate-200"
              >
                Watch workflow
              </Link>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-800 bg-slate-950/60 p-6">
            <div className="space-y-4">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
                  Live status
                </p>
                <p className="mt-2 text-lg font-semibold text-slate-100">
                  Processing 68%
                </p>
                <div className="mt-3 h-2 w-full rounded-full bg-slate-900">
                  <div className="h-2 w-[68%] rounded-full bg-emerald-500/70" />
                </div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
                <p className="text-sm font-semibold text-slate-200">
                  Suggested clips
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  6 candidates ready for review
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="rounded-full border border-emerald-500/40 px-3 py-1 text-xs text-emerald-200">
                    00:42 - 01:10
                  </span>
                  <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400">
                    03:18 - 03:56
                  </span>
                  <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400">
                    05:04 - 05:44
                  </span>
                </div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
                <p className="text-sm font-semibold text-slate-200">Clip render</p>
                <p className="mt-1 text-xs text-slate-500">
                  Preview ready to download
                </p>
                <button
                  type="button"
                  className="mt-4 w-full rounded-full border border-slate-700 px-4 py-2 text-xs text-slate-300"
                >
                  Download preview
                </button>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="rounded-2xl border border-slate-800 bg-slate-950/60 p-6"
            >
              <p className="text-lg font-semibold text-slate-100">
                {feature.title}
              </p>
              <p className="mt-2 text-sm text-slate-400">{feature.description}</p>
            </div>
          ))}
        </section>

        <section
          id="workflow"
          className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-center"
        >
          <div className="space-y-4">
            <p className="text-sm uppercase tracking-[0.3em] text-slate-500">
              Workflow
            </p>
            <h2 className="text-3xl font-semibold text-slate-100">
              Keep the team focused on the message.
            </h2>
            <p className="text-sm text-slate-400">
              From first upload to final render, every step stays visible. That
              means fewer handoff errors and more time to refine the story.
            </p>
            <Link
              href="/app"
              className="inline-flex items-center gap-2 text-sm text-emerald-300 hover:text-emerald-200"
            >
              Explore the dashboard
              <span aria-hidden="true">-&gt;</span>
            </Link>
          </div>
          <div className="grid gap-3">
            {STEPS.map((step) => (
              <div
                key={step.title}
                className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5"
              >
                <p className="text-sm font-semibold text-slate-100">{step.title}</p>
                <p className="mt-1 text-xs text-slate-400">{step.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-3xl border border-slate-800 bg-slate-950/70 p-8 text-center">
          <p className="text-sm uppercase tracking-[0.3em] text-slate-500">
            Ready to start
          </p>
          <h2 className="mt-3 text-3xl font-semibold text-slate-100">
            Your next sermon clip is one upload away.
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Launch the dashboard and keep everything in one place.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link
              href="/app"
              className="rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-slate-900 transition hover:bg-emerald-400"
            >
              Launch app
            </Link>
            <Link
              href="/app"
              className="rounded-full border border-slate-700 px-6 py-3 text-sm text-slate-200"
            >
              View uploads
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
