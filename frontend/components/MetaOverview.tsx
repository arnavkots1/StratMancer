'use client'

import Image from 'next/image'
import { m } from 'framer-motion'
import { Sparkles } from 'lucide-react'
import PatchSelector from './PatchSelector'
import { getChampionImageUrl } from '../lib/championImages'
import { fadeUp, scaleIn } from '../lib/motion'
import { MetaSnapshot, Elo } from '@/types'

interface MetaOverviewProps {
  meta: MetaSnapshot | null
  loading: boolean
  selectedElo: Elo
  onEloChange: (_elo: Elo) => void
  selectedPatch?: string
  onPatchChange: (_patch: string) => void
}

const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`

export default function MetaOverview({
  meta,
  loading,
  selectedElo,
  onEloChange,
  selectedPatch,
  onPatchChange,
}: MetaOverviewProps) {
  const availablePatches = meta?.available_patches ?? []
  const topChampions = meta?.champions.slice(0, 3) ?? []
  const lastUpdated = meta ? new Date(meta.last_updated).toLocaleString() : '—'

  return (
    <m.section
      variants={fadeUp}
      className="relative overflow-hidden rounded-[32px] border border-white/10 bg-[#0d1424]/85 p-6 backdrop-blur-xl"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(124,58,237,0.18),transparent_60%)] opacity-80" />
      <div className="relative space-y-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <p className="text-xs uppercase tracking-[0.28em] text-white/40">Meta Overview</p>
            <h2 className="text-3xl font-semibold text-white">
              Patch {meta?.patch ?? selectedPatch ?? '—'}
            </h2>
            <p className="text-sm text-white/60">
              Last updated {lastUpdated} · {meta?.total_matches ?? 0} matches analyzed
            </p>
          </div>
          <div className="w-full max-w-xl">
            <PatchSelector
              selectedElo={selectedElo}
              onEloChange={onEloChange}
              selectedPatch={selectedPatch ?? meta?.patch}
              onPatchChange={onPatchChange}
              patches={availablePatches}
              disabled={loading}
            />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {loading
            ? Array.from({ length: 3 }).map((_, index) => (
                <div
                  key={index}
                  className="h-40 rounded-2xl border border-white/10 bg-black/30"
                >
                  <div className="h-full animate-pulse rounded-2xl bg-white/10" />
                </div>
              ))
            : topChampions.map((champion, index) => (
                <m.div
                  key={champion.champion_id}
                  variants={scaleIn}
                  className="group relative overflow-hidden rounded-2xl border border-white/10 bg-[#10172a]/80 p-5 transition"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-primary/15 via-transparent to-secondary/15 opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
                  <div className="relative flex items-start justify-between gap-4">
                    <div>
                      <span className="text-xs uppercase tracking-[0.28em] text-white/40">#{index + 1}</span>
                      <h3 className="mt-1 text-lg font-semibold text-white">{champion.champion_name}</h3>
                      <p className="mt-1 text-sm text-white/60">
                        Win {formatPercent(champion.win_rate)} · Pick {formatPercent(champion.pick_rate)}
                      </p>
                    </div>
                    <div className="relative h-14 w-14 overflow-hidden rounded-xl border border-white/10 bg-black/30">
                      <Image
                        src={getChampionImageUrl(champion.champion_name)}
                        alt={champion.champion_name}
                        fill
                        sizes="80px"
                        className="object-cover transition duration-500 group-hover:scale-105"
                      />
                    </div>
                  </div>
                  <div className="relative mt-5 flex items-center justify-between text-sm text-white/70">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-accent" />
                      <span>Performance Index</span>
                    </div>
                    <span className="text-emerald-300">
                      {(champion.performance_index * 100).toFixed(1)}
                    </span>
                  </div>
                </m.div>
              ))}
        </div>
      </div>
    </m.section>
  )
}
