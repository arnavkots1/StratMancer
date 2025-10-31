'use client';

import { useEffect, useState } from 'react';
import { m } from 'framer-motion';
import Link from 'next/link';
import { Sparkles, TrendingUp, TrendingDown, Shield, Zap, Activity, Loader2, AlertCircle, ArrowLeft } from 'lucide-react';
import { Container } from '@/components/Section';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

// Inline motion variants (same as meta page)
const EASE_EXPO = [0.16, 1, 0.3, 1];
const EASE_SINE = [0.12, 0.32, 0.24, 1];

const fadeUp = {
  initial: { opacity: 0, y: 32 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: EASE_EXPO },
  },
  exit: {
    opacity: 0,
    y: -24,
    transition: { duration: 0.35, ease: EASE_SINE },
  },
};

const scaleIn = {
  initial: { opacity: 0, scale: 0.88, filter: 'blur(6px)' },
  animate: {
    opacity: 1,
    scale: 1,
    filter: 'blur(0px)',
    transition: { duration: 0.6, ease: EASE_EXPO },
  },
  exit: {
    opacity: 0,
    scale: 0.94,
    filter: 'blur(4px)',
    transition: { duration: 0.3, ease: EASE_SINE },
  },
};

const stagger = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

// Inline API client
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

interface PatchChampion {
  name: string;
  category: 'Buff' | 'Nerf' | 'Adjust';
  impact: number;
  affected_tags: string[];
  notes: string;
}

interface PatchFeatures {
  patch: string;
  champions: PatchChampion[];
  source: 'gemini' | 'heuristic' | 'none';
  priors: Record<string, { impact: number; tags: string[]; category: string; notes: string }>;
  message?: string;
}

type FilterType = 'All' | 'Buffed' | 'Nerfed' | 'Adjusted';

const TAG_COLORS: Record<string, string> = {
  damage: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
  burst: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  mobility: 'bg-sky-500/20 text-sky-300 border-sky-500/30',
  survivability: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  healing: 'bg-green-500/20 text-green-300 border-green-500/30',
  scaling: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  cc: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  ability_haste: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
};

export default function PatchNotesPage() {
  const [selectedPatch, setSelectedPatch] = useState<string>('14.21');
  const [features, setFeatures] = useState<PatchFeatures | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterType>('All');

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    fetch(`${API_BASE}/meta/patchnotes/${selectedPatch}`, {
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then(async (res) => {
        if (!res.ok) {
          if (res.status === 404) {
            throw new Error(`No patch notes available for patch ${selectedPatch}`);
          }
          throw new Error(`Failed to load patch notes: ${res.statusText}`);
        }
        return res.json();
      })
      .then((data) => {
        if (controller.signal.aborted) return;
        setFeatures(data);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setError(err.message || 'Failed to load patch notes');
        setFeatures(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [selectedPatch]);

  // Filter out invalid champion names (common words that aren't champions)
  const invalidNames = new Set([
    'Game', 'Potential', 'Negative', 'While', 'Addition', 'Objective', 'Base', 'Health',
    'Armor', 'Mana', 'Damage', 'Passive', 'Cooldown', 'Bonus', 'Vision', 'Hand', 'Demon',
    'Changes', 'Demonic', 'Fixed', 'Believe', 'Nerfs', 'Buffs', 'Auto', 'Asol'
  ]);

  const filteredChampions = features?.champions
    .filter((champ) => {
      // Filter by category
      if (filter === 'All') return true;
      if (filter === 'Buffed') return champ.category === 'Buff';
      if (filter === 'Nerfed') return champ.category === 'Nerf';
      if (filter === 'Adjusted') return champ.category === 'Adjust';
      return true;
    })
    .filter((champ) => {
      // Filter out invalid names (only if using heuristic)
      if (features?.source === 'heuristic' && invalidNames.has(champ.name)) {
        return false;
      }
      return true;
    }) || [];

  const ImpactArc = ({ impact, size = 48 }: { impact: number; size?: number }) => {
    const normalized = Math.max(-1, Math.min(1, impact / 100));
    const percentage = Math.abs(normalized * 100);
    const isPositive = normalized > 0;
    const strokeDasharray = `${(percentage / 100) * 251.2} 251.2`; // 2πr where r=40

    return (
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={size / 2 - 4}
            fill="none"
            stroke="rgba(255,255,255,0.1)"
            strokeWidth="4"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={size / 2 - 4}
            fill="none"
            stroke={isPositive ? '#10b981' : '#ef4444'}
            strokeWidth="4"
            strokeDasharray={strokeDasharray}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`text-xs font-semibold ${isPositive ? 'text-emerald-300' : 'text-rose-300'}`}>
            {isPositive ? '+' : ''}{normalized.toFixed(1)}%
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#060911]">
      <Container size="xl" className="py-16 lg:py-20">
        <m.div initial="initial" animate="animate" variants={fadeUp} className="space-y-10">
          {/* Header */}
          <m.section
            variants={scaleIn}
            className="relative overflow-hidden rounded-[32px] border border-white/10 bg-[#0d1424]/85 p-8 backdrop-blur-xl"
          >
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(124,58,237,0.18),transparent_60%)] opacity-80" />
            <div className="relative flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-3">
                <div className="flex items-center gap-4 flex-wrap">
                  <Link 
                    href="/meta" 
                    className="text-xs uppercase tracking-[0.28em] text-white/40 hover:text-primary/70 transition-colors flex items-center gap-1"
                  >
                    <ArrowLeft className="h-3 w-3" />
                    Meta Dashboard
                  </Link>
                  <span className="text-xs uppercase tracking-[0.28em] text-white/40">Patch Notes</span>
                  {features?.source === 'gemini' && (
                    <Badge className="bg-gradient-to-r from-purple-500/20 to-cyan-500/20 text-purple-200 border-purple-500/30 text-[10px] px-2 py-0.5 animate-pulse">
                      <Sparkles className="h-3 w-3 mr-1" />
                      AI: Gemini
                    </Badge>
                  )}
                  {features?.source === 'heuristic' && (
                    <Badge className="bg-amber-500/20 text-amber-200 border-amber-500/30 text-[10px] px-2 py-0.5">
                      <AlertCircle className="h-3 w-3 mr-1" />
                      Heuristic (Gemini recommended)
                    </Badge>
                  )}
                  {features?.message && (
                    <Badge variant="outline" className="border-rose-500/30 text-rose-200 text-[10px] px-2 py-0.5">
                      {features.message}
                    </Badge>
                  )}
                </div>
                <h1 className="text-3xl font-semibold text-white">
                  Patch {selectedPatch} Highlights
                </h1>
                <p className="max-w-xl text-sm text-white/60">
                  {features?.source === 'gemini'
                    ? 'AI-parsed champion changes with impact scores and meta tags. Automatically extracted from Riot\'s official patch notes using Gemini AI.'
                    : 'Champion changes extracted from patch notes. For best results, set GEMINI_API_KEY to enable AI-powered parsing.'}
                </p>
              </div>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={selectedPatch}
                  onChange={(e) => setSelectedPatch(e.target.value)}
                  placeholder="14.21"
                  className="px-4 py-2 rounded-lg border border-white/10 bg-black/30 text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-primary/40"
                />
                <Button
                  onClick={() => setSelectedPatch(selectedPatch)}
                  className="bg-gradient-to-r from-primary/60 to-secondary/60"
                >
                  Load Patch
                </Button>
              </div>
            </div>
          </m.section>

          {/* Filters */}
          <m.div variants={fadeUp} className="flex gap-2">
            {(['All', 'Buffed', 'Nerfed', 'Adjusted'] as FilterType[]).map((f) => (
              <Button
                key={f}
                onClick={() => setFilter(f)}
                variant={filter === f ? 'default' : 'outline'}
                className={
                  filter === f
                    ? 'bg-gradient-to-r from-primary/60 to-secondary/60 border-primary/40'
                    : 'border-white/10 bg-black/30'
                }
              >
                {f}
              </Button>
            ))}
          </m.div>

          {/* Error State */}
          {error && (
            <m.div
              variants={fadeUp}
              className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 flex items-center gap-3"
            >
              <AlertCircle className="h-5 w-5 text-rose-300" />
              <span className="text-rose-200">{error}</span>
            </m.div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          )}

          {/* Champion Grid */}
          {features && !loading && (
            <m.div
              variants={stagger}
              initial="initial"
              animate="animate"
              className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
            >
              {filteredChampions.map((champion, idx) => {
                const isBuff = champion.category === 'Buff';
                const isNerf = champion.category === 'Nerf';
                const glowColor = isBuff
                  ? 'from-emerald-500/20 to-emerald-600/10'
                  : isNerf
                    ? 'from-rose-500/20 to-rose-600/10'
                    : 'from-amber-500/20 to-amber-600/10';

                return (
                  <m.div
                    key={`${champion.name}-${idx}`}
                    variants={scaleIn}
                    className="group relative"
                  >
                    <Card className="relative overflow-hidden border border-white/10 bg-[#0d1424]/85 backdrop-blur-xl hover:border-primary/40 transition-all duration-300">
                      <div className={`absolute inset-0 bg-gradient-to-br ${glowColor} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
                      <div className="relative p-6 space-y-4">
                        {/* Header */}
                        <div className="flex items-start justify-between">
                          <div className="space-y-1">
                            <h3 className="text-lg font-semibold text-white">{champion.name}</h3>
                            <Badge
                              className={
                                isBuff
                                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                                  : isNerf
                                    ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                                    : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                              }
                            >
                              {champion.category}
                            </Badge>
                          </div>
                          <ImpactArc impact={champion.impact} />
                        </div>

                        {/* Tags */}
                        {champion.affected_tags.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            {champion.affected_tags.map((tag) => (
                              <Badge
                                key={tag}
                                variant="outline"
                                className={`text-xs ${TAG_COLORS[tag] || 'bg-white/10 text-white/70 border-white/20'}`}
                              >
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}

                        {/* Notes */}
                        {champion.notes && (
                          <p className="text-sm text-white/70 line-clamp-2">{champion.notes}</p>
                        )}
                      </div>
                    </Card>
                  </m.div>
                );
              })}
            </m.div>
          )}

          {/* Empty State */}
          {features && !loading && filteredChampions.length === 0 && (
            <m.div variants={fadeUp} className="text-center py-20 space-y-4">
              <p className="text-white/60">
                {features.champions.length === 0
                  ? 'No patch note data available for this patch.'
                  : 'No champions match the selected filter or all entries were filtered as invalid.'}
              </p>
              {features.source === 'heuristic' && features.champions.length > 0 && (
                <p className="text-xs text-amber-300/60">
                  Tip: Enable Gemini AI for accurate champion name extraction. Many heuristic entries are being filtered out.
                </p>
              )}
            </m.div>
          )}

          {/* Stats */}
          {features && !loading && filteredChampions.length > 0 && (
            <m.div variants={fadeUp} className="flex items-center gap-4 text-sm text-white/60">
              <span>Showing {filteredChampions.length} of {features.champions.length} entries</span>
              {features.source === 'heuristic' && (
                <span className="text-amber-300/60">• Using basic parsing - Gemini AI recommended</span>
              )}
            </m.div>
          )}
        </m.div>
      </Container>
    </div>
  );
}

