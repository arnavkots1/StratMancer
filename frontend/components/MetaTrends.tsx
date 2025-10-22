'use client'

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import { m } from 'framer-motion'
import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import type { MetaTrends as MetaTrendsType } from '@/types'
import { fadeUp } from '@/lib/motion'

interface MetaTrendsProps {
  trends: MetaTrendsType | null
  loading: boolean
}

const formatPercent = (value: number) => `${value.toFixed(2)}%`

export default function MetaTrends({ trends, loading }: MetaTrendsProps) {
  const risers = (trends?.risers ?? []).map((entry) => ({
    ...entry,
    deltaPercent: entry.delta_win_rate * 100,
  }))
  const fallers = (trends?.fallers ?? []).map((entry) => ({
    ...entry,
    deltaPercent: entry.delta_win_rate * 100,
  }))

  return (
    <m.section
      variants={fadeUp}
      className="relative overflow-hidden rounded-[28px] border border-white/10 bg-[#0d1424]/85 p-6 backdrop-blur-xl"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(6,182,212,0.18),transparent_60%)] opacity-70" />
      <div className="relative space-y-6">
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-semibold text-white">Trends</h3>
          <p className="text-sm text-white/60">
            Patch transition {trends?.previous_patch ?? '—'} → {trends?.latest_patch ?? '—'}
          </p>
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/20 border-t-accent" />
          </div>
        ) : risers.length === 0 && fallers.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-black/30 p-6 text-center text-sm text-white/60">
            Not enough historical data to compute patch-over-patch trends yet.
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            <TrendChart title="Top Risers" data={risers} color="#34d399" positive />
            <TrendChart title="Top Fallers" data={fallers} color="#f87171" />
          </div>
        )}
      </div>
    </m.section>
  )
}

interface TrendChartProps {
  title: string
  data: Array<{ champion_name: string; deltaPercent: number }>
  color: string
  positive?: boolean
}

function TrendChart({ title, data, color, positive = false }: TrendChartProps) {
  const displayData = data.map((item) => ({
    name: item.champion_name,
    delta: positive ? Math.abs(item.deltaPercent) : -Math.abs(item.deltaPercent),
  }))

  const Icon = positive ? ArrowUpRight : ArrowDownRight

  return (
    <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
      <div className="mb-4 flex items-center justify-between text-sm text-white/70">
        <div className="flex items-center gap-2">
          <Icon className={positive ? 'h-4 w-4 text-emerald-300' : 'h-4 w-4 text-rose-300'} />
          <span>{title}</span>
        </div>
        <span className="text-xs uppercase tracking-[0.28em] text-white/40">Δ Win %</span>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={displayData} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 16 }}>
            <defs>
              <linearGradient id={`trend-${title}`} x1="0" x2="1" y1="0" y2="0">
                <stop offset="0%" stopColor={color} stopOpacity={0.4} />
                <stop offset="100%" stopColor={color} stopOpacity={1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis
              type="number"
              stroke="rgba(255,255,255,0.5)"
              tickFormatter={(value) => formatPercent(Math.abs(value))}
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
                if (!active || !payload || payload.length === 0) return null
                const entry = payload[0]
                const deltaValue = Math.abs(entry.value as number)
                return (
                  <div className="rounded-lg border border-white/10 bg-[#10172a]/95 px-3 py-2 text-xs text-white/80">
                    <p className="font-semibold text-white">{entry.payload?.name}</p>
                    <p>{formatPercent(deltaValue)}</p>
                  </div>
                )
              }}
            />
            <Bar
              dataKey="delta"
              fill={`url(#trend-${title})`}
              radius={8}
              isAnimationActive
              animationDuration={900}
              animationEasing="ease-out"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
