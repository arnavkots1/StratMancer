'use client'

import { useMemo, useState, type ReactNode } from 'react'
import clsx from 'clsx'
import { Shield, Sparkles, Sword } from 'lucide-react'
import type { MetaChampion } from '@/types'

interface MetaTableProps {
  champions: MetaChampion[]
  loading: boolean
}

type SortKey = keyof Pick<
  MetaChampion,
  'performance_index' | 'win_rate' | 'pick_rate' | 'ban_rate' | 'delta_win_rate' | 'champion_name'
>

type FocusFilter = 'all' | 'impact' | 'control' | 'wildcard'

const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`

export default function MetaTable({ champions, loading }: MetaTableProps) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('performance_index')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [focus, setFocus] = useState<FocusFilter>('all')

  const filtered = useMemo(() => {
    const searchTerm = search.trim().toLowerCase()

    let base = champions ?? []

    if (searchTerm) {
      base = base.filter((champion) => champion.champion_name.toLowerCase().includes(searchTerm))
    }

    base = base.filter((champion) => {
      switch (focus) {
        case 'impact':
          return champion.performance_index >= 0.55 && champion.win_rate >= 0.51
        case 'control':
          return champion.ban_rate >= 0.15
        case 'wildcard':
          return Math.abs(champion.delta_win_rate) >= 0.015
        default:
          return true
      }
    })

    const sorted = [...base].sort((a, b) => {
      const first = a[sortKey]
      const second = b[sortKey]

      if (typeof first === 'string' && typeof second === 'string') {
        return sortDir === 'asc' ? first.localeCompare(second) : second.localeCompare(first)
      }

      const diff = (second as number) - (first as number)
      return sortDir === 'asc' ? -diff : diff
    })

    return sorted
  }, [champions, search, sortKey, sortDir, focus])

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir(key === 'champion_name' ? 'asc' : 'desc')
    }
  }

  return (
    <section className="relative overflow-hidden rounded-[32px] border border-white/10 bg-[#0d1424]/85 p-6 backdrop-blur-xl">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(124,58,237,0.18),transparent_60%)] opacity-70" />
      <div className="relative space-y-6">
        <header className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-white">Champion Meta</h3>
            <p className="text-sm text-white/60">Search or filter to focus on specific archetypes.</p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search champion..."
              className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-2 text-sm text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-primary/30 sm:w-56"
            />
            <FocusSegment focus={focus} onFocusChange={setFocus} />
          </div>
        </header>

        <div className="overflow-hidden rounded-2xl border border-white/10">
          <table className="min-w-full divide-y divide-white/10 text-sm text-white/80">
            <thead className="bg-white/5 text-xs uppercase tracking-[0.28em] text-white/40">
              <tr>
                <TableHeader
                  label="Champion"
                  active={sortKey === 'champion_name'}
                  direction={sortDir}
                  onClick={() => handleSort('champion_name')}
                />
                <TableHeader
                  label="Pick %"
                  active={sortKey === 'pick_rate'}
                  direction={sortDir}
                  onClick={() => handleSort('pick_rate')}
                />
                <TableHeader
                  label="Win %"
                  active={sortKey === 'win_rate'}
                  direction={sortDir}
                  onClick={() => handleSort('win_rate')}
                />
                <TableHeader
                  label="Ban %"
                  active={sortKey === 'ban_rate'}
                  direction={sortDir}
                  onClick={() => handleSort('ban_rate')}
                />
                <TableHeader
                  label="Δ Win %"
                  active={sortKey === 'delta_win_rate'}
                  direction={sortDir}
                  onClick={() => handleSort('delta_win_rate')}
                />
                <TableHeader
                  label="Performance"
                  active={sortKey === 'performance_index'}
                  direction={sortDir}
                  onClick={() => handleSort('performance_index')}
                />
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10 bg-black/20">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-10 text-center text-white/60">
                    <div className="mx-auto h-2 w-48 animate-pulse rounded-full bg-white/10" />
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-10 text-center text-white/60">
                    No champions match your filters.
                  </td>
                </tr>
              ) : (
                filtered.map((champion) => (
                  <tr key={champion.champion_id} className="transition hover:bg-white/5">
                    <td className="px-4 py-3 font-medium text-white/90">{champion.champion_name}</td>
                    <td className="px-4 py-3">{formatPercent(champion.pick_rate)}</td>
                    <td className="px-4 py-3">{formatPercent(champion.win_rate)}</td>
                    <td className="px-4 py-3">{formatPercent(champion.ban_rate)}</td>
                    <td
                      className={clsx('px-4 py-3 font-semibold', {
                        'text-emerald-300': champion.delta_win_rate > 0.0001,
                        'text-rose-300': champion.delta_win_rate < -0.0001,
                        'text-white/70': Math.abs(champion.delta_win_rate) <= 0.0001,
                      })}
                    >
                      {formatPercent(champion.delta_win_rate)}
                    </td>
                    <td className="px-4 py-3 text-white/80">
                      {(champion.performance_index * 100).toFixed(2)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

interface FocusSegmentProps {
  focus: FocusFilter
  onFocusChange: (_focus: FocusFilter) => void
}

function FocusSegment({ focus, onFocusChange }: FocusSegmentProps) {
  return (
    <div className="flex overflow-hidden rounded-full border border-white/10 bg-black/30 text-xs uppercase tracking-[0.28em] text-white/50">
      <FocusButton
        isActive={focus === 'all'}
        icon={<Sparkles className="h-4 w-4" />}
        label="All"
        onClick={() => onFocusChange('all')}
      />
      <FocusButton
        isActive={focus === 'impact'}
        icon={<Sword className="h-4 w-4" />}
        label="Impact"
        onClick={() => onFocusChange('impact')}
      />
      <FocusButton
        isActive={focus === 'control'}
        icon={<Shield className="h-4 w-4" />}
        label="Control"
        onClick={() => onFocusChange('control')}
      />
      <FocusButton
        isActive={focus === 'wildcard'}
        icon={<Sparkles className="h-4 w-4" />}
        label="Wildcard"
        onClick={() => onFocusChange('wildcard')}
      />
    </div>
  )
}

interface FocusButtonProps {
  isActive: boolean
  icon: ReactNode
  label: string
  onClick: () => void
}

function FocusButton({ isActive, icon, label, onClick }: FocusButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'flex flex-1 items-center justify-center gap-2 px-4 py-2 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40',
        isActive
          ? 'bg-white/10 text-white'
          : 'text-white/50 hover:bg-white/5 hover:text-white',
      )}
    >
      {icon}
      {label}
    </button>
  )
}

interface HeaderProps {
  label: string
  active: boolean
  direction: 'asc' | 'desc'
  onClick: () => void
}

function TableHeader({ label, active, direction, onClick }: HeaderProps) {
  return (
    <th
      scope="col"
      className={clsx(
        'cursor-pointer px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.28em] transition',
        active ? 'text-white' : 'text-white/45',
      )}
      onClick={onClick}
    >
      <div className="flex items-center gap-2">
        {label}
        {active && <span className="text-[10px] text-white/60">{direction === 'asc' ? '▲' : '▼'}</span>}
      </div>
    </th>
  )
}
