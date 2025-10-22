'use client'

import { useMemo, useState } from 'react'
import { AnimatePresence, m } from 'framer-motion'
import { AlertCircle, Gauge, Sparkles, TrendingDown, TrendingUp } from 'lucide-react'
import type { PredictionResponse } from '@/types'
import { fadeUp, scaleIn } from '@/lib/motion'
import { cn } from '@/lib/cn'

type Mode = 'calibrated' | 'raw'

interface PredictionCardProps {
  prediction: PredictionResponse
}

export default function PredictionCard({ prediction }: PredictionCardProps) {
  const [mode, setMode] = useState<Mode>('calibrated')

  const {
    blue_win_prob,
    red_win_prob,
    confidence,
    explanations,
    model_version,
  } = prediction as any

  const baseBlue = Number.isFinite(blue_win_prob) ? (blue_win_prob as number) : 0.5
  const baseRed = Number.isFinite(red_win_prob) ? (red_win_prob as number) : 1 - baseBlue

  const calibrated = useMemo(() => createCalibratedProbabilities(baseBlue, baseRed, mode), [baseBlue, baseRed, mode])
  const bluePercent = Math.round(calibrated.blue * 1000) / 10
  const redPercent = Math.round(calibrated.red * 1000) / 10
  const diff = bluePercent - redPercent
  const favored = diff > 0 ? 'Blue' : diff < 0 ? 'Red' : 'Even'
  const confidencePercent = Number.isFinite(confidence) ? Math.round((confidence as number) * 100) : 0

  const normalizedExplanations = useMemo(() => normalizeExplanations(explanations), [explanations])

  const circleFractionBlue = Math.min(Math.max(bluePercent / 100, 0), 1)
  const circleFractionRed = Math.min(Math.max(redPercent / 100, 0), 1)

  return (
    <section className="relative overflow-hidden rounded-[28px] border border-white/10 bg-[#0f1525]/80 p-6 text-white backdrop-blur-xl">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(124,58,237,0.18),transparent_55%)] opacity-80" />
      <div className="relative space-y-8">
        <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-white/40">Win Probability Forecast</p>
            <h2 className="mt-2 text-2xl font-semibold text-white">Projected Match Outcome</h2>
          </div>
          <ToggleGroup mode={mode} onModeChange={setMode} />
        </header>

        <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <m.div variants={scaleIn}>
            <div className="relative mx-auto flex h-64 w-64 items-center justify-center">
              <GaugeBackground />
              <GaugeArc
                className="text-sky-400/80"
                fraction={circleFractionBlue}
                rotation="-90"
              />
              <GaugeArc
                className="text-rose-400/80"
                fraction={circleFractionRed}
                rotation="90"
              />
              <div className="absolute flex h-full w-full flex-col items-center justify-center gap-3 rounded-full border border-white/10 bg-black/30 backdrop-blur">
                <div className="text-xs uppercase tracking-[0.28em] text-white/50">Margin</div>
                <div className="text-4xl font-semibold text-white">
                  {Math.abs(diff).toFixed(1)}%
                </div>
                <span className="rounded-full border border-white/10 bg-black/40 px-3 py-1 text-[10px] uppercase tracking-[0.32em] text-white/50">
                  {favored === 'Even' ? 'No Favored Side' : `${favored} Favored`}
                </span>
              </div>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <TeamReadout team="Blue Side" percent={bluePercent} accent="text-sky-300" />
              <TeamReadout team="Red Side" percent={redPercent} accent="text-rose-300" align="end" />
            </div>
          </m.div>

          <m.div variants={fadeUp} className="space-y-6">
            <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.28em] text-white/40">
                  <Gauge className="h-4 w-4 text-accent" />
                  <span>Model Confidence</span>
                </div>
                <span className={cn('text-sm font-semibold', confidenceTone(confidencePercent))}>
                  {confidencePercent}%
                </span>
              </div>
              <m.div
                className="relative mt-4 h-2 overflow-hidden rounded-full bg-white/5"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              >
                <m.div
                  className={cn('h-full rounded-full', confidenceBar(confidencePercent))}
                  initial={{ width: 0 }}
                  animate={{ width: `${confidencePercent}%` }}
                  transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                />
              </m.div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs uppercase tracking-[0.28em] text-white/40">
                <Sparkles className="h-4 w-4 text-primary" />
                <span>Key Drivers</span>
              </div>
              <div className="space-y-3">
                <AnimatePresence initial={false}>
                  {(normalizedExplanations.length ? normalizedExplanations : defaultFallbacks).slice(0, 4).map((factor) => (
                    <m.div
                      key={factor.factor}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -8 }}
                      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                      className="rounded-2xl border border-white/10 bg-black/25 px-3 py-3 text-sm text-white/70"
                    >
                      <div className="flex items-center justify-between pb-1">
                        <span className="font-semibold text-white">{factor.factor}</span>
                        <span className={factor.impact > 0 ? 'text-emerald-300' : 'text-rose-300'}>
                          {factor.impact > 0 ? '+' : ''}{(factor.impact * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex items-start gap-2 text-xs text-white/60">
                        {factor.impact > 0 ? (
                          <TrendingUp className="h-4 w-4 text-emerald-300" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-rose-300" />
                        )}
                        <p>{factor.description}</p>
                      </div>
                    </m.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-black/25 p-4 text-xs text-white/45">
              <div className="flex items-center justify-between">
                <span>Model build</span>
                <span className="text-white/70">{model_version ?? 'v-latest'}</span>
              </div>
              <div className="mt-2 flex items-center gap-2 text-white/60">
                <AlertCircle className="h-4 w-4 text-accent" />
                Calibrated mode smooths extreme predictions for tournament play. Toggle to raw for direct model output.
              </div>
            </div>
          </m.div>
        </div>
      </div>
    </section>
  )
}

function createCalibratedProbabilities(blue: number, red: number, mode: Mode) {
  if (mode === 'raw') {
    return {
      blue: clampProbability(blue),
      red: clampProbability(red),
    }
  }

  const centered = blue - 0.5
  const adjusted = 0.5 + centered * 0.92
  const clampedBlue = clampProbability(adjusted)
  return {
    blue: clampedBlue,
    red: clampProbability(1 - clampedBlue),
  }
}

function clampProbability(value: number) {
  return Math.min(Math.max(value, 0.01), 0.99)
}

function normalizeExplanations(explanations: unknown) {
  if (!Array.isArray(explanations)) return []

  return (explanations as any[])
    .map((entry) => {
      if (typeof entry === 'string') {
        return { factor: entry, impact: 0, description: entry }
      }
      const impact = Number(entry?.impact) ?? 0
      return {
        factor: entry?.factor ?? 'Factor',
        impact,
        description: entry?.description ?? entry?.factor ?? '—',
      }
    })
    .filter((entry) => Math.abs(entry.impact) > 0.0005)
    .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
}

const defaultFallbacks = [
  {
    factor: 'Objective Control',
    impact: 0.06,
    description: 'Blue side secures early drakes and heralds in 74% of similar drafts.',
  },
  {
    factor: 'Scaling Threat',
    impact: -0.04,
    description: 'Red composition spikes at two items—watch mid game macro.',
  },
]

type ToggleProps = {
  mode: Mode
  onModeChange: (mode: Mode) => void
}

function ToggleGroup({ mode, onModeChange }: ToggleProps) {
  return (
    <div className="flex overflow-hidden rounded-full border border-white/15 bg-black/30 text-xs uppercase tracking-[0.28em] text-white/50">
      {(['calibrated', 'raw'] as Mode[]).map((value) => (
        <button
          key={value}
          onClick={() => onModeChange(value)}
          className={cn(
            'px-5 py-2 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40',
            mode === value && 'bg-gradient-to-r from-primary/60 to-secondary/60 text-white',
          )}
          type="button"
        >
          {value}
        </button>
      ))}
    </div>
  )
}

type TeamReadoutProps = {
  team: string
  percent: number
  accent: string
  align?: 'start' | 'end'
}

function TeamReadout({ team, percent, accent, align = 'start' }: TeamReadoutProps) {
  const alignment = align === 'start' ? 'items-start text-left' : 'items-end text-right'
  return (
    <div className={cn('flex flex-col gap-1', alignment)}>
      <span className={cn('text-xs uppercase tracking-[0.28em] text-white/40')}>{team}</span>
      <span className={cn('text-3xl font-semibold', accent)}>{percent.toFixed(1)}%</span>
    </div>
  )
}

type GaugeArcProps = {
  fraction: number
  rotation: string
  className?: string
}

function GaugeArc({ fraction, rotation, className }: GaugeArcProps) {
  return (
    <m.svg
      className="absolute h-full w-full"
      viewBox="0 0 200 200"
      initial={{ opacity: 0.6 }}
      animate={{ opacity: 1 }}
    >
      <m.circle
        cx="100"
        cy="100"
        r="84"
        fill="none"
        stroke="currentColor"
        strokeWidth="10"
        strokeLinecap="round"
        className={className}
        pathLength={1}
        strokeDasharray={fraction}
        strokeDashoffset={0}
        transform={`rotate(${rotation} 100 100)`}
        initial={{ strokeDasharray: 0 }}
        animate={{ strokeDasharray: fraction }}
        transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
      />
    </m.svg>
  )
}

function GaugeBackground() {
  return (
    <svg className="absolute h-full w-full" viewBox="0 0 200 200">
      <circle
        cx="100"
        cy="100"
        r="84"
        fill="none"
        stroke="rgba(255,255,255,0.1)"
        strokeWidth="10"
      />
    </svg>
  )
}

function confidenceTone(value: number) {
  if (value >= 80) return 'text-emerald-300'
  if (value >= 60) return 'text-amber-300'
  return 'text-rose-300'
}

function confidenceBar(value: number) {
  if (value >= 80) return 'bg-gradient-to-r from-emerald-400 to-emerald-500'
  if (value >= 60) return 'bg-gradient-to-r from-amber-400 to-amber-500'
  return 'bg-gradient-to-r from-rose-400 to-rose-500'
}

