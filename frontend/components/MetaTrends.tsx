'use client';

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

import { MetaTrends } from '@/types';

interface MetaTrendsProps {
  trends: MetaTrends | null;
  loading: boolean;
}

const formatPercent = (value: number) => `${value.toFixed(2)}%`;

export default function MetaTrends({ trends, loading }: MetaTrendsProps) {
  const risers = (trends?.risers ?? []).map(entry => ({
    ...entry,
    deltaPercent: entry.delta_win_rate * 100,
  }));
  const fallers = (trends?.fallers ?? []).map(entry => ({
    ...entry,
    deltaPercent: entry.delta_win_rate * 100,
  }));

  return (
    <section className="rounded-3xl bg-white/8 p-6 shadow-lg shadow-black/20 backdrop-blur">
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-semibold text-white">Trends</h3>
        <p className="text-sm text-white/60">
          Patch transition {trends?.previous_patch ?? '—'} → {trends?.latest_patch ?? '—'}
        </p>
      </div>

      {loading ? (
        <div className="mt-6 flex h-64 items-center justify-center">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/20 border-t-white" />
        </div>
      ) : risers.length === 0 && fallers.length === 0 ? (
        <div className="mt-8 rounded-2xl border border-white/10 bg-white/5 p-6 text-center text-white/60">
          Not enough historical data to compute patch-over-patch trends yet.
        </div>
      ) : (
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <TrendChart title="Top Risers" data={risers} color="#34d399" positive />
          <TrendChart title="Top Fallers" data={fallers} color="#f87171" />
        </div>
      )}
    </section>
  );
}

interface TrendChartProps {
  title: string;
  data: Array<{ champion_name: string; deltaPercent: number }>;
  color: string;
  positive?: boolean;
}

function TrendChart({ title, data, color, positive = false }: TrendChartProps) {
  const displayData = data.map(item => ({
    name: item.champion_name,
    delta: positive ? Math.abs(item.deltaPercent) : -Math.abs(item.deltaPercent),
  }));

  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 shadow-inner shadow-black/30">
      <h4 className="text-sm font-semibold uppercase tracking-wide text-white/60">{title}</h4>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={displayData} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis
              type="number"
              stroke="rgba(255,255,255,0.5)"
              tickFormatter={value => formatPercent(Math.abs(value))}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={120}
              stroke="rgba(255,255,255,0.5)"
              tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }}
            />
            <Tooltip
              cursor={{ fill: 'rgba(148, 163, 184, 0.15)' }}
              content={({ active, payload }) => {
                if (!active || !payload || payload.length === 0) return null;
                const entry = payload[0];
                const deltaValue = Math.abs(entry.value as number);
                return (
                  <div className="rounded-lg border border-white/10 bg-slate-900/95 px-3 py-2 text-xs text-white">
                    <p className="font-semibold">{entry.payload?.name}</p>
                    <p>{formatPercent(deltaValue)}</p>
                  </div>
                );
              }}
            />
            <Bar
              dataKey="delta"
              fill={color}
              radius={6}
              isAnimationActive
              animationDuration={800}
              animationEasing="ease-out"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

