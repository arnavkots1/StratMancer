import Link from 'next/link'
import {
  ArrowRight,
  Zap,
  TrendingUp,
  Shield,
  Sparkles,
  Cpu,
  Target
} from 'lucide-react'

const featureHighlights = [
  {
    title: 'Real-Time Draft IQ',
    description:
      'Instant win probability updates keep pace with champion select, reacting in under 500ms as picks lock in.',
    icon: Zap
  },
  {
    title: 'Explainable Insights',
    description:
      'Surface synergies, counterpicks, and role gaps so analysts and captains understand exactly why a draft wins.',
    icon: TrendingUp
  },
  {
    title: 'Grounded in Live Data',
    description:
      'Models learn from curated Gold-rank matches collected via the Riot API, refreshed every new patch.',
    icon: Shield
  }
] as const

const workflowSteps = [
  {
    step: '01',
    title: 'Collect High-Elo Matches',
    description:
      'The pipeline ingests fresh queues through the Riot API, normalizes metadata, and stores it in Parquet.',
    icon: Target
  },
  {
    step: '02',
    title: 'Score Each Champion Select',
    description:
      'ML models evaluate comps in real time, balancing role coverage, engage tools, and patch trends.',
    icon: Cpu
  },
  {
    step: '03',
    title: 'Ship Insights to Analysts',
    description:
      'The web client and API expose probabilities, matchup notes, and actionable suggestions for every slot.',
    icon: TrendingUp
  }
] as const

const statHighlights = [
  { label: 'Champions Tracked', value: '163', sublabel: 'Updated each patch' },
  { label: 'Gold Queue Matches', value: '100+', sublabel: 'Per refresh cycle' },
  { label: 'Average Response', value: '<500ms', sublabel: 'Draft predictions' },
  { label: 'Insight Coverage', value: '100%', sublabel: 'Roles, synergies, bans' }
] as const

const heroHighlights = [
  'Adaptive champion suggestions tuned for ranked and scrim environments.',
  'Blend of statistical win rates and comp heuristics to prevent one-trick drafts.',
  'Seamless handoff between analysts and players through a shared draft board.'
] as const

const samplePicks = [
  { champion: 'Aatrox', boost: '+5%' },
  { champion: 'Vi', boost: '+4%' },
  { champion: 'Ahri', boost: '+6%' },
  { champion: 'Kai\'Sa', boost: '+3%' },
  { champion: 'Rell', boost: '+5%' }
] as const

const sampleBans = [
  { champion: 'Zed', note: 'mid threat' },
  { champion: 'Maokai', note: 'teamfight denial' },
  { champion: 'Vayne', note: 'late game spike' }
] as const

export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(217,169,68,0.18),_transparent_55%)]" />
      <div className="absolute inset-y-0 right-[-40%] -z-10 h-[120%] w-[70%] rounded-full bg-[conic-gradient(from_120deg_at_50%_50%,rgba(217,169,68,0.25),transparent_65%)] blur-3xl opacity-60" />

      <main className="relative mx-auto flex max-w-7xl flex-col gap-24 px-6 py-24 md:px-10 lg:px-16">
        <section className="relative isolate overflow-hidden rounded-3xl border border-gold-900/40 bg-black/40 px-8 py-16 shadow-[0_0_120px_-40px_rgba(217,169,68,0.55)] backdrop-blur sm:px-12 sm:py-20">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(255,220,110,0.12),_transparent_60%)]" />
          <div className="grid items-center gap-12 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-gold-500/40 bg-gold-900/30 px-4 py-1 text-xs uppercase tracking-[0.35em] text-gold-100">
                <Sparkles className="h-4 w-4 text-gold-300" />
                Draft smarter
              </div>
              <h1 className="mt-6 text-4xl font-semibold leading-tight sm:text-5xl md:text-6xl">
                <span className="bg-gradient-to-r from-gold-400 via-gold-200 to-gold-500 bg-clip-text text-transparent">
                  Master the Draft Phase
                </span>
              </h1>
              <p className="mt-6 text-lg text-gray-300 sm:text-xl">
                StratMancer blends live Riot data with machine learning to guide every pick and ban. Empower coaches and players with a shared, data-backed draft board built for high-stakes League of Legends.
              </p>

              <ul className="mt-8 space-y-4 text-sm text-gray-300 sm:text-base">
                {heroHighlights.map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <Shield className="mt-1 h-5 w-5 text-gold-400" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-10 flex flex-wrap items-center gap-4">
                <Link
                  href="/draft"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-gold-500 px-6 py-3 text-base font-semibold text-gray-900 transition hover:bg-gold-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-950"
                >
                  Launch Draft Analyzer
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <a
                  href="https://github.com/arnavparuthi/StratMancer"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-gold-500/50 px-6 py-3 text-base font-semibold text-gold-200 transition hover:border-gold-400 hover:text-gold-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-950"
                >
                  Explore the stack
                </a>
              </div>
            </div>

            <div className="relative h-full">
              <div className="absolute right-6 top-6 h-24 w-24 rounded-full bg-gold-500/10 blur-2xl" />
              <div className="relative overflow-hidden rounded-3xl border border-gold-700/40 bg-gradient-to-br from-gray-900 via-gray-950 to-gray-900 p-8 shadow-2xl shadow-gold-900/30">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase tracking-[0.3em] text-gray-500">
                    Draft room
                  </span>
                  <span className="rounded-full bg-gold-500/20 px-3 py-1 text-xs font-medium text-gold-200">
                    Win chance 62%
                  </span>
                </div>
                <div className="mt-6 space-y-4">
                  <div className="flex items-center justify-between rounded-2xl bg-gray-900/60 px-4 py-3">
                    <div>
                      <p className="text-sm text-gray-400">Blue Side</p>
                      <p className="text-lg font-semibold text-gray-100">Flex Engage Comp</p>
                    </div>
                    <span className="text-sm text-gold-200">+8 synergy</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="space-y-3 rounded-2xl border border-gray-800 bg-gray-900/40 p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Picks</p>
                      <div className="space-y-2 text-gray-300">
                        {samplePicks.map(({ champion, boost }) => (
                          <div key={champion} className="flex items-center justify-between">
                            <span>{champion}</span>
                            <span className="text-xs text-gold-300">{boost}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="space-y-3 rounded-2xl border border-gray-800 bg-gray-900/40 p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Bans</p>
                      <div className="space-y-2 text-gray-300">
                        {sampleBans.map(({ champion, note }) => (
                          <div key={champion} className="flex items-center justify-between">
                            <span>{champion}</span>
                            <span className="text-xs text-gold-300">{note}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="rounded-2xl border border-gray-800 bg-gray-900/60 p-5">
                    <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Insight</p>
                    <p className="mt-3 text-sm text-gray-300">
                      Prioritize long-range engage to punish immobile carries. Consider banning disengage tools to preserve flank threat.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {statHighlights.map((stat) => (
              <div
                key={stat.label}
                className="rounded-2xl border border-gray-800 bg-gray-900/50 p-6 text-center shadow-lg shadow-black/30"
              >
                <div className="text-3xl font-semibold text-gold-300">{stat.value}</div>
                <div className="mt-2 text-sm text-gray-400">{stat.label}</div>
                <div className="text-xs uppercase tracking-[0.2em] text-gray-600">{stat.sublabel}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-10">
          <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
            <div>
              <p className="text-sm uppercase tracking-[0.4em] text-gold-200">Why StratMancer</p>
              <h2 className="mt-3 text-3xl font-semibold text-gray-100 sm:text-4xl">
                Built for draft rooms that demand clarity and speed
              </h2>
            </div>
            <Link
              href="/draft"
              className="inline-flex items-center gap-2 rounded-xl border border-gold-500/40 px-4 py-2 text-sm font-semibold text-gold-200 transition hover:border-gold-400 hover:text-gold-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-950"
            >
              Try the interactive draft
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {featureHighlights.map(({ title, description, icon: Icon }) => (
              <article
                key={title}
                className="group relative overflow-hidden rounded-2xl border border-gray-800 bg-gray-900/60 p-8 shadow-xl shadow-black/30 transition hover:-translate-y-1 hover:border-gold-500/40"
              >
                <div className="absolute inset-0 opacity-0 transition group-hover:opacity-100">
                  <div className="absolute inset-0 bg-gradient-to-br from-gold-500/10 via-transparent to-transparent" />
                </div>
                <div className="relative">
                  <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gold-500/10 text-gold-300">
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-100">{title}</h3>
                  <p className="mt-3 text-sm text-gray-400">{description}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="space-y-12">
          <div className="text-center">
            <p className="text-sm uppercase tracking-[0.35em] text-gold-200">Pipeline</p>
            <h2 className="mt-3 text-3xl font-semibold text-gray-100 sm:text-4xl">
              From live data to ready-to-call plays
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-sm text-gray-400 sm:text-base">
              Automatons handle the heavy lifting so analysts can focus on strategy. Each stage is observable and documented for both engineers and coaching staff.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {workflowSteps.map(({ step, title, description, icon: Icon }) => (
              <div
                key={title}
                className="relative overflow-hidden rounded-2xl border border-gray-800 bg-gray-900/60 p-8 shadow-lg shadow-black/30"
              >
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(217,169,68,0.12),_transparent_70%)] opacity-0 transition hover:opacity-100" />
                <div className="relative flex flex-col gap-5">
                  <span className="inline-flex w-12 items-center justify-center rounded-full border border-gold-500/40 bg-gold-500/10 text-sm font-semibold text-gold-200">
                    {step}
                  </span>
                  <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gold-500/10 text-gold-300">
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-100">{title}</h3>
                  <p className="text-sm text-gray-400">{description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="overflow-hidden rounded-3xl border border-gold-900/30 bg-black/40 px-8 py-16 shadow-[0_0_90px_-40px_rgba(217,169,68,0.5)] backdrop-blur sm:px-12">
          <div className="grid gap-10 md:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] md:items-center">
            <div>
              <h2 className="text-3xl font-semibold text-gray-100 sm:text-4xl">
                Ready to draft with confidence?
              </h2>
              <p className="mt-4 text-sm text-gray-400 sm:text-base">
                Fire up the analyzer before your next scrim or review session. Start with prebuilt datasets or connect your own collection pipeline straight from the StratMancer backend.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-4">
                <Link
                  href="/draft"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-gold-500 px-6 py-3 text-base font-semibold text-gray-900 transition hover:bg-gold-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-950"
                >
                  Start drafting
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <a
                  href="https://github.com/arnavparuthi/StratMancer#readme"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-gold-500/40 px-6 py-3 text-base font-semibold text-gold-200 transition hover:border-gold-400 hover:text-gold-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-950"
                >
                  View setup guide
                </a>
              </div>
            </div>
            <div className="relative rounded-2xl border border-gold-700/30 bg-gradient-to-br from-gray-900/80 via-gray-950/80 to-gray-900/80 p-6 shadow-[inset_0_1px_0_rgba(217,169,68,0.25)]">
              <div className="space-y-4 text-sm text-gray-300">
                <div className="flex items-center justify-between border-b border-gray-800 pb-4">
                  <span className="text-xs uppercase tracking-[0.3em] text-gray-500">
                    Quick start
                  </span>
                  <span className="rounded-full bg-gold-500/15 px-3 py-1 text-xs font-medium text-gold-200">
                    5 minutes
                  </span>
                </div>
                <div>
                  <p className="font-semibold text-gray-100">Install dependencies</p>
                  <pre className="mt-2 rounded-lg bg-gray-950/70 px-4 py-3 text-xs text-gray-400">
                    <code>pip install -r requirements.txt</code>
                  </pre>
                </div>
                <div>
                  <p className="font-semibold text-gray-100">Generate demo dataset</p>
                  <pre className="mt-2 rounded-lg bg-gray-950/70 px-4 py-3 text-xs text-gray-400">
                    <code>python quickstart.py</code>
                  </pre>
                </div>
                <div>
                  <p className="font-semibold text-gray-100">Launch the analyzer</p>
                  <pre className="mt-2 rounded-lg bg-gray-950/70 px-4 py-3 text-xs text-gray-400">
                    <code>npm run dev</code>
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

