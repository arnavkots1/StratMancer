'use client';

import { Elo } from '@/types';

interface PatchSelectorProps {
  selectedElo: Elo;
  onEloChange: (elo: Elo) => void;
  selectedPatch?: string;
  onPatchChange: (patch: string) => void;
  patches: string[];
  disabled?: boolean;
}

const eloLabels: Record<Elo, string> = {
  low: 'Low (Iron–Silver)',
  mid: 'Mid (Gold–Emerald)',
  high: 'High (Diamond+)',
};

export default function PatchSelector({
  selectedElo,
  onEloChange,
  selectedPatch,
  onPatchChange,
  patches,
  disabled = false,
}: PatchSelectorProps) {
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-end">
      <label className="flex w-full items-center gap-2 md:w-auto">
        <span className="text-sm font-medium text-slate-200">ELO</span>
        <select
          value={selectedElo}
          onChange={event => onEloChange(event.target.value as Elo)}
          disabled={disabled}
          className="w-full rounded-lg border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-100 backdrop-blur transition hover:border-white/30 focus:border-white/60 focus:outline-none md:w-56"
        >
          {(Object.keys(eloLabels) as Elo[]).map(elo => (
            <option key={elo} value={elo} className="bg-slate-900 text-slate-100">
              {eloLabels[elo]}
            </option>
          ))}
        </select>
      </label>

      <label className="flex w-full items-center gap-2 md:w-auto">
        <span className="text-sm font-medium text-slate-200">Patch</span>
        <select
          value={selectedPatch ?? ''}
          onChange={event => onPatchChange(event.target.value)}
          disabled={disabled || patches.length === 0}
          className="w-full rounded-lg border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-100 backdrop-blur transition hover:border-white/30 focus:border-white/60 focus:outline-none md:w-40"
        >
          {patches.length === 0 ? (
            <option value="" disabled>
              No data
            </option>
          ) : (
            patches.map(patch => (
              <option key={patch} value={patch} className="bg-slate-900 text-slate-100">
                {patch}
              </option>
            ))
          )}
        </select>
      </label>
    </div>
  );
}

