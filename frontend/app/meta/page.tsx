'use client';

import { useEffect, useState, type ReactNode } from 'react';
import { m } from 'framer-motion';
import { TrendingUp, AlertCircle, Gauge, Activity } from 'lucide-react';
import dynamic from 'next/dynamic';

// Lazy load heavy components
const MetaOverview = dynamic(() => import('@/components/MetaOverview'), {
  loading: () => <div className="flex items-center justify-center p-8"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>,
  ssr: false
});

const MetaTable = dynamic(() => import('@/components/MetaTable'), {
  loading: () => <div className="flex items-center justify-center p-8"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>,
  ssr: false
});

const MetaTrends = dynamic(() => import('@/components/MetaTrends'), {
  loading: () => <div className="flex items-center justify-center p-8"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>,
  ssr: false
});
import { Container } from '@/components/Section';
import { api } from '../../lib/api';
import { fadeUp, scaleIn } from '../../lib/motion';
import { DataWarning } from '@/components/DataWarning';
import type { Elo, MetaSnapshot, MetaTrends as MetaTrendsType } from '@/types';

const DEFAULT_ELO: Elo = 'mid';

export default function MetaPage() {
  const [selectedElo, setSelectedElo] = useState<Elo>(DEFAULT_ELO);
  const [selectedPatch, setSelectedPatch] = useState<string | undefined>(undefined);

  const [meta, setMeta] = useState<MetaSnapshot | null>(null);
  const [trends, setTrends] = useState<MetaTrendsType | null>(null);

  const [metaLoading, setMetaLoading] = useState<boolean>(true);
  const [trendsLoading, setTrendsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setMetaLoading(true);

    const metaPromise = selectedPatch 
      ? api.getMetaForPatch(selectedElo, selectedPatch)
      : api.getMetaOverview(selectedElo);
    
    metaPromise
      .then(data => {
        if (cancelled) return;
        const metaData = data as MetaSnapshot;
        setMeta(metaData);
        setError(null);
        if (!selectedPatch || selectedPatch !== metaData.patch) {
          setSelectedPatch(metaData.patch);
        }
      })
      .catch(err => {
        if (cancelled) return;
        setError(err.message || 'Failed to load meta data');
        setMeta(null);
      })
      .finally(() => {
        if (!cancelled) {
          setMetaLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedElo, selectedPatch]);

  useEffect(() => {
    let cancelled = false;
    setTrendsLoading(true);

    api
      .getMetaTrends(selectedElo)
      .then(data => {
        if (cancelled) return;
        setTrends(data as MetaTrendsType);
      })
      .catch(() => {
        if (cancelled) return;
        setTrends(null);
      })
      .finally(() => {
        if (!cancelled) {
          setTrendsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedElo]);

  const handleEloChange = (elo: Elo) => {
    setSelectedElo(elo);
    setSelectedPatch(undefined);
  };

  const totalChampions = meta?.champions.length ?? 0

  return (
    <div className="min-h-screen bg-[#060911]">
      <Container size="xl" className="py-16 lg:py-20">
        <m.div initial="initial" animate="animate" variants={fadeUp} className="space-y-10">
          <m.section
            variants={scaleIn}
            className="relative overflow-hidden rounded-[32px] border border-white/10 bg-[#0d1424]/85 p-8 backdrop-blur-xl"
          >
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(124,58,237,0.18),transparent_60%)] opacity-80" />
            <div className="relative flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-3">
                <span className="text-xs uppercase tracking-[0.28em] text-white/40">Meta Dashboard</span>
                <h1 className="text-3xl font-semibold text-white">Rift Trends Insight</h1>
                <p className="max-w-xl text-sm text-white/60">
                  Compare balance swings across patches, surface high-impact champions, and calibrate your draft prep using live ladder telemetry.
                </p>
              </div>
              <div className="grid w-full gap-4 sm:grid-cols-3 lg:w-auto">
                <MetricPill icon={<TrendingUp className="h-4 w-4 text-emerald-300" />} label="Active Champions" value={`${totalChampions}`} />
                <MetricPill icon={<Gauge className="h-4 w-4 text-accent" />} label="Selected ELO" value={selectedElo.toUpperCase()} />
                <MetricPill icon={<Activity className="h-4 w-4 text-sky-300" />} label="Matches" value={`${meta?.total_matches ?? 0}`} />
              </div>
            </div>
          </m.section>

          {/* Data Warning */}
          <DataWarning variant="warning" />

          {error && (
            <m.div
              variants={fadeUp}
              className="flex items-center gap-3 rounded-2xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-200"
            >
              <AlertCircle className="h-5 w-5" />
              <span>{error}</span>
            </m.div>
          )}

          <MetaOverview
            meta={meta}
            loading={metaLoading}
            selectedElo={selectedElo}
            onEloChange={handleEloChange}
            selectedPatch={selectedPatch}
            onPatchChange={(patch) => setSelectedPatch(patch || undefined)}
          />

          <m.section variants={fadeUp} className="grid gap-8 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
            <MetaTable champions={meta?.champions ?? []} loading={metaLoading} />
            <MetaTrends trends={trends} loading={trendsLoading} />
          </m.section>
        </m.div>
      </Container>
    </div>
  )
}

type MetricPillProps = {
  icon: ReactNode
  label: string
  value: string
}

function MetricPill({ icon, label, value }: MetricPillProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-white/70 backdrop-blur">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.28em] text-white/40">
        {icon}
        <span>{label}</span>
      </div>
      <div className="mt-2 text-lg font-semibold text-white/85">{value}</div>
    </div>
  )
}
