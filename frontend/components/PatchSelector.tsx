'use client'

import type { ElementType } from 'react'
import { Trophy, ShieldHalf, Sparkles } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '../lib/cn'
import { Elo } from '@/types'

interface PatchSelectorProps {
  selectedElo: Elo
  onEloChange: (_elo: Elo) => void
  selectedPatch?: string
  onPatchChange: (_patch: string) => void
  patches: string[]
  disabled?: boolean
}

const eloConfig: Array<{ value: Elo; label: string; icon: ElementType }> = [
  { value: 'low', label: 'Iron–Silver', icon: ShieldHalf },
  { value: 'mid', label: 'Gold–Emerald', icon: Sparkles },
  { value: 'high', label: 'Diamond+', icon: Trophy },
]

export default function PatchSelector({
  selectedElo,
  onEloChange,
  selectedPatch,
  onPatchChange,
  patches,
  disabled = false,
}: PatchSelectorProps) {
  return (
    <div className="flex flex-col gap-4">
      <Tabs value={selectedElo} onValueChange={(value) => onEloChange(value as Elo)}>
        <TabsList className="grid w-full grid-cols-3 rounded-2xl border border-white/10 bg-black/40 p-1">
          {eloConfig.map(({ value, label, icon: Icon }) => (
            <TabsTrigger
              key={value}
              value={value}
              disabled={disabled}
              className="flex items-center justify-center gap-2 rounded-xl border border-transparent px-3 py-2 text-xs uppercase tracking-[0.28em] text-white/60 data-[state=active]:border-white/20 data-[state=active]:bg-white/10 data-[state=active]:text-white"
            >
              <Icon className="h-4 w-4" />
              {label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <div className="flex flex-col gap-2">
        <span className="text-xs uppercase tracking-[0.28em] text-white/40">Patch</span>
        <div className="flex flex-wrap gap-2 rounded-2xl border border-white/10 bg-black/30 p-2">
          {patches.length === 0 ? (
            <button className="w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-xs uppercase tracking-[0.28em] text-white/40" disabled>
              No data
            </button>
          ) : (
            patches.map((patch) => (
              <button
                key={patch}
                type="button"
                onClick={() => onPatchChange(patch)}
                disabled={disabled}
                className={cn(
                  'rounded-xl border border-white/10 px-4 py-2 text-xs uppercase tracking-[0.28em] text-white/60 transition',
                  selectedPatch === patch && 'border-white/25 bg-white/10 text-white',
                )}
              >
                {patch}
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

