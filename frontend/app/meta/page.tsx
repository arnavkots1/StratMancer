'use client';

import { useEffect, useState } from 'react';

import MetaOverview from '@/components/MetaOverview';
import MetaTable from '@/components/MetaTable';
import MetaTrends from '@/components/MetaTrends';
import { api } from '@/lib/api';
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
        setMeta(data);
        setError(null);
        if (!selectedPatch || selectedPatch !== data.patch) {
          setSelectedPatch(data.patch);
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
        setTrends(data);
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

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Meta Tracker</h1>
          <p className="text-gray-400">
            Track champion performance across ELO brackets with live pick, win, and ban rates
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/20 border border-red-800 rounded-lg text-red-400">
            {error}
          </div>
        )}

      <main className="mx-auto max-w-7xl pb-16">
        <div className="space-y-8">
          <MetaOverview
            meta={meta}
            loading={metaLoading}
            selectedElo={selectedElo}
            onEloChange={handleEloChange}
            selectedPatch={selectedPatch}
            onPatchChange={patch => setSelectedPatch(patch || undefined)}
          />

          {error && (
            <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {error}
            </div>
          )}

          <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
            <MetaTable champions={meta?.champions ?? []} loading={metaLoading} />
            <MetaTrends trends={trends} loading={trendsLoading} />
          </div>
        </div>
      </main>
      </div>
    </div>
  );
}
