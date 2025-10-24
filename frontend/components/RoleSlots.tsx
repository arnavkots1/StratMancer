'use client';

import { Ban, X } from 'lucide-react';
import type { Champion, TeamComposition, Team, Role } from '@/types';
import { getChampionImageUrl } from '@/lib/championImages';

interface RoleSlotsProps {
  team: Team;
  composition: TeamComposition;
  bans: Champion[];
  onUpdateComposition: (composition: TeamComposition) => void;
  onUpdateBans: (bans: Champion[]) => void;
  currentDraftAction?: { team: 'blue' | 'red'; action: 'ban' | 'pick'; role?: keyof TeamComposition } | null;
}

const ROLES: { key: keyof TeamComposition; label: string }[] = [
  { key: 'top', label: 'Top' },
  { key: 'jungle', label: 'Jungle' },
  { key: 'mid', label: 'Mid' },
  { key: 'adc', label: 'ADC' },
  { key: 'support', label: 'Support' },
];

export default function RoleSlots({
  team,
  composition,
  bans,
  onUpdateComposition,
  onUpdateBans,
  currentDraftAction,
}: RoleSlotsProps) {
  const teamColor = team === 'blue' ? 'blue' : 'red';
  const _teamName = team === 'blue' ? 'Blue Team' : 'Red Team';

  const removeChampion = (role: keyof TeamComposition) => {
    onUpdateComposition({
      ...composition,
      [role]: null,
    });
  };

  const removeBan = (index: number) => {
    onUpdateBans(bans.filter((_, i) => i !== index));
  };

  return (
    <>
      {/* Role Slots */}
      <div className="space-y-3 mb-6">
        {ROLES.map(({ key, label }) => {
          const champion = composition[key];
          const isCurrentPick = currentDraftAction?.team === team && 
                                currentDraftAction?.action === 'pick' && 
                                currentDraftAction?.role === key;
          return (
            <div key={key} className="flex items-center space-x-3">
              <div className="w-20 text-sm font-medium text-gray-400">
                {label}
              </div>
              
              <div 
                className={`role-slot ${champion ? 'filled' : ''} ${isCurrentPick ? 'ring-4 ring-gold-500 animate-pulse' : ''} ${teamColor} flex-1 relative`}
                title={champion ? champion.name : label}
              >
                {champion ? (
                  <>
                    {/* Champion Image */}
                    <img
                      src={getChampionImageUrl(champion.name)}
                      alt={champion.name}
                      className="absolute inset-0 w-full h-full object-cover rounded-lg"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                        e.currentTarget.nextElementSibling?.classList.remove('hidden');
                      }}
                    />
                    
                    {/* Fallback placeholder */}
                    <div className="hidden absolute inset-0 flex items-center justify-center bg-gradient-to-br from-gray-700 to-gray-900 rounded-lg">
                      <span className="text-2xl font-bold text-gray-600">
                        {champion.name.charAt(0)}
                      </span>
                    </div>
                    
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent rounded-lg" />
                    <div className="absolute bottom-1 left-0 right-0 text-center">
                      <div className="text-xs font-semibold text-white truncate px-1 drop-shadow-lg">
                        {champion.name}
                      </div>
                    </div>
                    <button
                      onClick={() => removeChampion(key)}
                      className="absolute -top-2 -right-2 w-6 h-6 bg-red-600 rounded-full flex items-center justify-center hover:bg-red-500 transition-colors z-10 shadow-lg"
                      title="Remove"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </>
                ) : isCurrentPick ? (
                  <div className="flex flex-col items-center justify-center h-full">
                    <span className="text-gold-500 text-sm font-bold animate-pulse">👉 PICK NOW</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <span className="text-gray-700 text-xs">—</span>
                  </div>
                )}
              </div>

              {/* Tags */}
              {champion && (
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap gap-1">
                    {(() => {
                      const damageArray = Array.isArray(champion.tags.damage) 
                        ? champion.tags.damage 
                        : (champion.tags.damage ? [champion.tags.damage] : []);
                      return damageArray.slice(0, 2).map((tag, idx) => (
                        <span key={`${champion.id}-damage-${tag}-${idx}`} className="badge badge-neutral text-xs">
                          {tag}
                        </span>
                      ));
                    })()}
                    {champion.tags.engage !== undefined && (
                      <span className="badge badge-positive text-xs">
                        Engage: {champion.tags.engage}
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Bans */}
      <div>
        <div className="flex items-center space-x-2 mb-3">
          <Ban className="w-4 h-4 text-gray-400" />
          <h3 className="text-sm font-medium">Bans ({bans.length}/5)</h3>
        </div>

        <div className="flex space-x-2">
          {Array.from({ length: 5 }).map((_, index) => {
            const ban = bans[index];
            const isCurrentBan = currentDraftAction?.team === team && 
                                 currentDraftAction?.action === 'ban' && 
                                 bans.length === index;
            return (
              <div
                key={index}
                className={`role-slot w-14 h-14 ${ban ? 'filled' : ''} ${isCurrentBan ? 'ring-4 ring-gold-500 animate-pulse' : ''} relative`}
                title={ban ? ban.name : 'Ban slot'}
              >
                {ban ? (
                  <>
                    {/* Champion Image */}
                    <img
                      src={getChampionImageUrl(ban.name)}
                      alt={ban.name}
                      className="absolute inset-0 w-full h-full object-cover rounded-lg grayscale"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                        e.currentTarget.nextElementSibling?.classList.remove('hidden');
                      }}
                    />
                    
                    {/* Fallback placeholder */}
                    <div className="hidden absolute inset-0 flex items-center justify-center bg-gradient-to-br from-gray-700 to-gray-900 rounded-lg">
                      <span className="text-lg font-bold text-gray-600">
                        {ban.name.charAt(0)}
                      </span>
                    </div>
                    
                    <div className="absolute inset-0 flex items-center justify-center bg-black/40 rounded-lg">
                      <Ban className="w-6 h-6 text-red-500 drop-shadow-lg" />
                    </div>
                    <button
                      onClick={() => removeBan(index)}
                      className="absolute -top-1 -right-1 w-5 h-5 bg-red-600 rounded-full flex items-center justify-center hover:bg-red-500 transition-colors z-10 shadow-lg"
                      title="Remove ban"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </>
                ) : isCurrentBan ? (
                  <div className="flex flex-col items-center justify-center">
                    <Ban className="w-6 h-6 text-gold-500 animate-pulse" />
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center">
                    <Ban className="w-5 h-5 text-gray-800" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Team Stats Summary */}
      <div className="mt-6 pt-6 border-t border-gray-800">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-xs text-gray-400 mb-1">Engage</div>
            <div className="text-lg font-bold text-gold-500">
              {Object.values(composition)
                .filter(Boolean)
                .reduce((sum, c) => sum + (c!.tags.engage || 0), 0)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">CC</div>
            <div className="text-lg font-bold text-gold-500">
              {Object.values(composition)
                .filter(Boolean)
                .reduce((sum, c) => sum + (c!.tags.hard_cc || 0), 0)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">Sustain</div>
            <div className="text-lg font-bold text-gold-500">
              {Object.values(composition)
                .filter(Boolean)
                .reduce((sum, c) => sum + (c!.tags.sustain || 0), 0)}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

