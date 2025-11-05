'use client';

import { useEffect, useState, type ReactNode } from 'react';
import Link from 'next/link';
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
// Inline API client to avoid import issues
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

type RequestOptions = {
  signal?: AbortSignal;
  timeoutMs?: number;
  revalidate?: number | false;
  method?: string;
  body?: string;
  headers?: Record<string, string>;
};

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function withTimeout(signal?: AbortSignal, timeoutMs = 30_000) {
  if (signal) return signal;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const { signal: controllerSignal } = controller;
  controllerSignal.addEventListener('abort', () => clearTimeout(timer));
  return controllerSignal;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { timeoutMs, ...rest } = options;
  const signal = await withTimeout(rest.signal, timeoutMs);
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...rest,
    signal,
    headers: {
      'Content-Type': 'application/json',
      'X-STRATMANCER-KEY': process.env.NEXT_PUBLIC_API_KEY || 'dev-key-change-in-production',
      ...(rest.headers ?? {}),
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new ApiError(message || 'API request failed', response.status);
  }

  if (response.status === 204) {
    return null as T;
  }

  return (await response.json()) as T;
}

const api = {
  predictDraft(payload: Record<string, unknown>, options?: RequestOptions) {
    return request('/predict-draft', { method: 'POST', body: JSON.stringify(payload), ...options });
  },
  refreshContext(elo?: string, options?: RequestOptions) {
    return request('/predict-draft/refresh-context', { 
      method: 'POST', 
      body: JSON.stringify({ elo }), 
      ...options 
    });
  },
  getPickRecommendations(payload: Record<string, unknown>, options?: RequestOptions) {
    return request('/recommend/pick', { method: 'POST', body: JSON.stringify(payload), ...options });
  },
  getBanRecommendations(payload: Record<string, unknown>, options?: RequestOptions) {
    return request('/recommend/ban', { method: 'POST', body: JSON.stringify(payload), ...options });
  },
  analyzeDraft(payload: Record<string, unknown>, options?: RequestOptions) {
    return request('/analysis/draft', { method: 'POST', body: JSON.stringify(payload), ...options });
  },
  getFeatureMap(options?: RequestOptions) {
    return request('/models/feature-map', { method: 'GET', ...options });
  },
  getMetaOverview(elo: string, options?: RequestOptions) {
    return request(`/meta/${elo}/latest`, { method: 'GET', ...options });
  },
  getMetaTrends(elo: string, options?: RequestOptions) {
    return request(`/meta/trends/${elo}`, { method: 'GET', ...options });
  },
  getMetaForPatch(elo: string, patch: string, options?: RequestOptions) {
    return request(`/meta/${elo}/${patch}`, { method: 'GET', ...options });
  },
  getModels(options?: RequestOptions) {
    return request('/models/registry', { method: 'GET', ...options });
  },
  getLandingData(options?: RequestOptions) {
    return request('/landing/', { method: 'GET', ...options });
  },
  health(options?: RequestOptions) {
    return request('/health', { method: 'GET', ...options });
  },
};

// Inline motion variants to avoid import issues
const EASE_EXPO = [0.16, 1, 0.3, 1]
const EASE_SINE = [0.12, 0.32, 0.24, 1]

const REDUCED_VARIANTS = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.2, ease: 'linear' } },
  exit: { opacity: 0, transition: { duration: 0.2, ease: 'linear' } },
}

function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function maybeReduce(variants: any): any {
  return prefersReducedMotion() ? REDUCED_VARIANTS : variants
}

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
}

const scaleIn = maybeReduce({
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
})
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
                <div className="flex items-center gap-4 flex-wrap">
                  <span className="text-xs uppercase tracking-[0.28em] text-white/40">Meta Dashboard</span>
                </div>
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
