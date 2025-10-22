'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, BarChart3, Zap, AlertCircle } from 'lucide-react';
import MetaOverview from '@/components/MetaOverview';
import MetaTable from '@/components/MetaTable';
import MetaTrends from '@/components/MetaTrends';
import { Glow } from '@/components/Glow';
import { Container } from '@/components/Section';
import { api } from '@/lib/api';
import { eliteMotionPresets } from '@/lib/motion';
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
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/10">
      <Container size="xl" className="py-8">
        <motion.div
          initial="initial"
          animate="animate"
          variants={eliteMotionPresets.page}
          className="max-w-7xl mx-auto space-y-8"
        >
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <Glow variant="secondary" className="rounded-2xl">
              <div className="glass-card p-6 border border-secondary-500/20">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-xl bg-secondary-500/10 border border-secondary-500/20">
                    <TrendingUp className="w-6 h-6 text-secondary-400" />
                  </div>
                  <h1 className="text-3xl font-bold">
                    <span className="gradient-text">Meta Tracker</span>
                  </h1>
                </div>
                <p className="text-muted-foreground">
                  Track champion performance across ELO brackets with live pick, win, and ban rates
                </p>
              </div>
            </Glow>
          </motion.div>

          {/* Error Display */}
          {error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <p className="text-destructive flex-1">{error}</p>
            </motion.div>
          )}

          {/* Main Content */}
          <div className="space-y-6">
            <MetaOverview
              meta={meta}
              loading={metaLoading}
              selectedElo={selectedElo}
              onEloChange={handleEloChange}
              selectedPatch={selectedPatch}
              onPatchChange={patch => setSelectedPatch(patch || undefined)}
            />

            <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
              <MetaTable champions={meta?.champions ?? []} loading={metaLoading} />
              <MetaTrends trends={trends} loading={trendsLoading} />
            </div>
          </div>
        </motion.div>
      </Container>
    </div>
  );
}
