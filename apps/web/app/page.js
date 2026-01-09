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
      <div className="pointer-events-none absolute left-[-120px] top-[-80px] h-56 w-56 rounded-full bg-[color:var(--accent-soft)] blur-3xl" />
      <div className="pointer-events-none absolute right-[-80px] top-40 h-64 w-64 rounded-full bg-[color:var(--accent-2-soft)] blur-3xl" />
      <div className="pointer-events-none absolute bottom-[-120px] left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-[#f6d7a8] blur-[140px]" />

      <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-14 px-6 py-14">
        <header className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[color:var(--accent-soft)] text-lg font-semibold text-[color:var(--accent-strong)]">
              SC
            </span>
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-[color:var(--muted)]">
                SermonClip Studio
              </p>
              <p className="text-sm font-semibold text-[color:var(--ink)]">
                Editorial clip workspace
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/app" className="btn btn-outline">
              Open app
            </Link>
            <Link href="/#workflow" className="btn btn-soft">
              See workflow
            </Link>
          </div>
        </header>

        <section className="grid gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div className="space-y-6">
            <span className="pill">Sermon clips</span>
            <h1 className="text-4xl leading-tight md:text-5xl">
              Shape sermons into{" "}
              <span className="text-[color:var(--accent-strong)]">
                shareable stories
              </span>{" "}
              with calm precision.
            </h1>
            <p className="max-w-xl text-base text-[color:var(--muted)]">
              A single space for uploads, transcription status, and clip delivery.
              Designed for focused teams and consistent branding.
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <Link href="/app" className="btn btn-primary">
                Launch dashboard
              </Link>
              <Link href="/app" className="btn btn-outline">
                View recent uploads
              </Link>
            </div>
          </div>

          <div className="surface-card p-6">
            <div className="space-y-4">
              <div className="surface-card-soft p-4">
                <p className="pill">Live status</p>
                <p className="mt-3 text-xl font-semibold text-[color:var(--ink)]">
                  Processing 68%
                </p>
                <div className="mt-4 h-2 w-full rounded-full bg-[color:var(--bg-elevated)]">
                  <div className="h-2 w-[68%] rounded-full bg-[color:var(--accent)]" />
                </div>
              </div>
              <div className="surface-card-soft p-4">
                <div className="flex items-center justify-between text-sm font-semibold">
                  <span>Suggested clips</span>
                  <span className="text-xs text-[color:var(--muted)]">6 ready</span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="rounded-full border border-[color:var(--accent)] px-3 py-1 text-xs text-[color:var(--accent-strong)]">
                    00:42 - 01:10
                  </span>
                  <span className="rounded-full border border-[color:var(--line)] px-3 py-1 text-xs text-[color:var(--muted)]">
                    03:18 - 03:56
                  </span>
                  <span className="rounded-full border border-[color:var(--line)] px-3 py-1 text-xs text-[color:var(--muted)]">
                    05:04 - 05:44
                  </span>
                </div>
              </div>
              <div className="surface-card-soft p-4">
                <div className="flex items-center justify-between text-sm font-semibold">
                  <span>Clip render</span>
                  <span className="text-xs text-[color:var(--muted)]">
                    Preview ready
                  </span>
                </div>
                <button type="button" className="btn btn-outline mt-4 w-full">
                  Download preview
                </button>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="surface-card p-6">
              <p className="text-lg font-semibold">{feature.title}</p>
              <p className="mt-2 text-sm text-[color:var(--muted)]">
                {feature.description}
              </p>
            </div>
          ))}
        </section>

        <section
          id="workflow"
          className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-center"
        >
          <div className="space-y-4">
            <span className="pill">Workflow</span>
            <h2 className="text-3xl">
              Keep the team focused on the message.
            </h2>
            <p className="text-sm text-[color:var(--muted)]">
              From first upload to final render, every milestone stays visible.
              Fewer handoff errors, more time to refine the story.
            </p>
            <Link href="/app" className="btn btn-secondary w-fit">
              Explore the dashboard
            </Link>
          </div>
          <div className="grid gap-3">
            {STEPS.map((step) => (
              <div key={step.title} className="surface-card-soft p-5">
                <p className="text-sm font-semibold">{step.title}</p>
                <p className="mt-1 text-xs text-[color:var(--muted)]">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section className="surface-card px-8 py-10 text-center">
          <span className="pill">Ready to start</span>
          <h2 className="mt-4 text-3xl">
            Your next sermon clip is one upload away.
          </h2>
          <p className="mt-2 text-sm text-[color:var(--muted)]">
            Launch the dashboard and keep everything in one place.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link href="/app" className="btn btn-primary">
              Launch app
            </Link>
            <Link href="/app" className="btn btn-outline">
              View uploads
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
