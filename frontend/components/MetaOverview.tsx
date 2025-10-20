'use client';

import { MetaSnapshot, Elo } from '@/types';
import PatchSelector from './PatchSelector';
import { Sparkles } from 'lucide-react';

interface MetaOverviewProps {
  meta: MetaSnapshot | null;
  loading: boolean;
  selectedElo: Elo;
  onEloChange: (elo: Elo) => void;
  selectedPatch?: string;
  onPatchChange: (patch: string) => void;
}

const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function MetaOverview({
  meta,
  loading,
  selectedElo,
  onEloChange,
  selectedPatch,
  onPatchChange,
}: MetaOverviewProps) {
  const availablePatches = meta?.available_patches ?? [];
  const topChampions = meta?.champions.slice(0, 3) ?? [];
  const lastUpdated = meta ? new Date(meta.last_updated).toLocaleString() : '--';

  return (
    <section className="rounded-3xl bg-white/10 p-6 shadow-xl shadow-blue-900/20 backdrop-blur">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide text-white/70">Meta Overview</p>
          <h2 className="mt-1 text-2xl font-semibold text-white">
            Patch {meta?.patch ?? selectedPatch ?? '—'}
          </h2>
          <p className="text-sm text-white/60">
            Last updated {lastUpdated} · {meta?.total_matches ?? 0} matches analyzed
          </p>
        </div>

        <PatchSelector
          selectedElo={selectedElo}
          onEloChange={onEloChange}
          selectedPatch={selectedPatch ?? meta?.patch}
          onPatchChange={onPatchChange}
          patches={availablePatches}
          disabled={loading}
        />
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {loading
          ? Array.from({ length: 3 }).map((_, index) => (
              <div
                key={index}
                className="h-32 rounded-2xl bg-white/5 p-4 shadow-inner shadow-black/40"
              >
                <div className="h-full animate-pulse rounded-xl bg-white/10" />
              </div>
            ))
          : topChampions.map((champion, index) => (
              <div
                key={champion.champion_id}
                className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900/80 to-slate-800/60 p-5 shadow-inner shadow-black/30"
              >
                <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500" />
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-white/60">#{index + 1}</p>
                    <h3 className="text-lg font-semibold text-white">
                      {champion.champion_name}
                    </h3>
                    <p className="mt-1 text-sm text-white/70">
                      Win {formatPercent(champion.win_rate)} · Pick {formatPercent(champion.pick_rate)}
                    </p>
                  </div>
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white">
                    <Sparkles className="h-5 w-5" />
                  </div>
                </div>
                <p className="mt-4 text-sm font-semibold text-emerald-300">
                  Performance Index {(champion.performance_index * 100).toFixed(1)}
                </p>
              </div>
            ))}
      </div>
    </section>
  );
}

