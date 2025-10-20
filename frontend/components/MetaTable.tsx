'use client';

import { useMemo, useState } from 'react';
import clsx from 'clsx';

import { MetaChampion } from '@/types';

interface MetaTableProps {
  champions: MetaChampion[];
  loading: boolean;
}

type SortKey = keyof Pick<
  MetaChampion,
  'performance_index' | 'win_rate' | 'pick_rate' | 'ban_rate' | 'delta_win_rate' | 'champion_name'
>;

const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function MetaTable({ champions, loading }: MetaTableProps) {
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('performance_index');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const filtered = useMemo(() => {
    const searchTerm = search.trim().toLowerCase();
    const base = champions ?? [];
    const filteredChampions = searchTerm
      ? base.filter(champion => champion.champion_name.toLowerCase().includes(searchTerm))
      : base;

    const sorted = [...filteredChampions].sort((a, b) => {
      const first = a[sortKey];
      const second = b[sortKey];

      if (typeof first === 'string' && typeof second === 'string') {
        return sortDir === 'asc'
          ? first.localeCompare(second)
          : second.localeCompare(first);
      }

      const diff = (second as number) - (first as number);
      return sortDir === 'asc' ? -diff : diff;
    });

    return sorted;
  }, [champions, search, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir(key === 'champion_name' ? 'asc' : 'desc');
    }
  };

  return (
    <section className="rounded-3xl bg-white/8 p-6 shadow-lg shadow-black/20 backdrop-blur">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <h3 className="text-lg font-semibold text-white">Champion Meta</h3>
        <input
          value={search}
          onChange={event => setSearch(event.target.value)}
          placeholder="Search champion..."
          className="w-full rounded-xl border border-white/10 bg-white/10 px-4 py-2 text-sm text-white placeholder:text-white/50 focus:border-white/50 focus:outline-none focus:ring-0 md:w-64"
        />
      </div>

      <div className="mt-4 overflow-hidden rounded-2xl border border-white/5">
        <table className="min-w-full divide-y divide-white/10 text-sm text-white">
          <thead className="bg-white/5">
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

          <tbody className="divide-y divide-white/5 bg-white/5">
            {loading ? (
              <tr>
                <td colSpan={6} className="py-10 text-center text-white/60">
                  <div className="mx-auto h-2 w-48 animate-pulse rounded-full bg-white/10" />
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-10 text-center text-white/60">
                  No champions match your search.
                </td>
              </tr>
            ) : (
              filtered.map(champion => (
                <tr key={champion.champion_id} className="transition hover:bg-white/5">
                  <td className="px-4 py-3 font-medium text-white">
                    {champion.champion_name}
                  </td>
                  <td className="px-4 py-3 text-white/80">{formatPercent(champion.pick_rate)}</td>
                  <td className="px-4 py-3 text-white/80">{formatPercent(champion.win_rate)}</td>
                  <td className="px-4 py-3 text-white/80">{formatPercent(champion.ban_rate)}</td>
                  <td
                    className={clsx('px-4 py-3 font-semibold', {
                      'text-emerald-400': champion.delta_win_rate > 0.0001,
                      'text-rose-400': champion.delta_win_rate < -0.0001,
                      'text-white/70': Math.abs(champion.delta_win_rate) <= 0.0001,
                    })}
                  >
                    {formatPercent(champion.delta_win_rate)}
                  </td>
                  <td className="px-4 py-3 text-white">
                    {(champion.performance_index * 100).toFixed(2)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

interface HeaderProps {
  label: string;
  active: boolean;
  direction: 'asc' | 'desc';
  onClick: () => void;
}

function TableHeader({ label, active, direction, onClick }: HeaderProps) {
  return (
    <th
      scope="col"
      className={clsx(
        'cursor-pointer px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-white/60 transition hover:text-white',
        active && 'text-white'
      )}
      onClick={onClick}
    >
      <div className="flex items-center gap-1">
        {label}
        {active && <span className="text-[10px]">{direction === 'asc' ? '▲' : '▼'}</span>}
      </div>
    </th>
  );
}
