'use client';

import { useState, useMemo } from 'react';
import { Search, X } from 'lucide-react';
import type { Champion, Role } from '@/types';
import { getChampionImageUrl } from '../lib/championImages';

interface ChampionPickerProps {
  champions: Champion[];
  selectedChampions: Champion[];
  bannedChampions: Champion[];
  onSelectChampion: (champion: Champion) => void;
  currentDraftAction?: { team: 'blue' | 'red'; action: 'ban' | 'pick'; role?: string } | null;
}

const ROLES: Role[] = ['TOP', 'JUNGLE', 'MID', 'ADC', 'SUPPORT'];

export default function ChampionPicker({
  champions,
  selectedChampions,
  bannedChampions,
  onSelectChampion,
  currentDraftAction,
}: ChampionPickerProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRole, setSelectedRole] = useState<Role | 'ALL'>('ALL');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  // Get all unique tags from champions
  const allTags = useMemo(() => {
    const tagSet = new Set<string>();
    champions.forEach(champ => {
      if (champ.tags.damage) {
        const damageArray = Array.isArray(champ.tags.damage) ? champ.tags.damage : [champ.tags.damage];
        damageArray.forEach(t => tagSet.add(t));
      }
      if (champ.tags.role) {
        const roleArray = Array.isArray(champ.tags.role) ? champ.tags.role : [champ.tags.role];
        roleArray.forEach(t => tagSet.add(t));
      }
    });
    return Array.from(tagSet).sort();
  }, [champions]);

  // Filter champions
  const filteredChampions = useMemo(() => {
    return champions.filter(champ => {
      // Search query
      if (searchQuery && !champ.name.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }

      // Role filter
      if (selectedRole !== 'ALL' && !champ.roles.includes(selectedRole)) {
        return false;
      }

      // Tag filters
      if (selectedTags.length > 0) {
        const damageArray = Array.isArray(champ.tags.damage) ? champ.tags.damage : (champ.tags.damage ? [champ.tags.damage] : []);
        const roleArray = Array.isArray(champ.tags.role) ? champ.tags.role : (champ.tags.role ? [champ.tags.role] : []);
        const champTags = [...damageArray, ...roleArray];
        if (!selectedTags.some(tag => champTags.includes(tag))) {
          return false;
        }
      }

      return true;
    });
  }, [champions, searchQuery, selectedRole, selectedTags]);

  const isChampionDisabled = (champion: Champion) => {
    return (
      selectedChampions.some(c => c.id === champion.id) ||
      bannedChampions.some(c => c.id === champion.id)
    );
  };

  const toggleTag = (tag: string) => {
    setSelectedTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  };

  return (
    <div className="card">
      <div className="mb-6">
        {currentDraftAction ? (
          <>
            <h2 className="text-xl font-bold mb-2 ml-4">
              <span className={currentDraftAction.team === 'blue' ? 'text-blue-400' : 'text-red-400'}>
                {currentDraftAction.team.toUpperCase()}
              </span>
              {' '}selecting{' '}
              {currentDraftAction.action === 'ban' ? 'BAN' : currentDraftAction.role?.toUpperCase()}
            </h2>
            <p className="text-sm text-gray-400 mb-4 ml-4">
              Click any champion below to {currentDraftAction.action === 'ban' ? 'ban' : 'pick'} it
            </p>
          </>
        ) : (
          <>
            <h2 className="text-xl font-bold mb-2 text-green-400">Draft Complete!</h2>
            <p className="text-sm text-gray-400 mb-4">
              All picks and bans are done. Click &quot;Analyze Draft&quot; above.
            </p>
          </>
        )}

        {/* Search */}
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search champions..."
              className="input pl-10"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* Role Filter */}
        <div className="mb-4 ml-4">
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium">Roles</label>
            {selectedRole !== 'ALL' && (
              <button
                onClick={() => setSelectedRole('ALL')}
                className="text-xs text-gray-400 hover:text-gray-300 transition-colors"
              >
                Clear selection
              </button>
            )}
          </div>
          <div className="flex items-center space-x-2 overflow-x-auto pb-2">
            <button
              onClick={() => setSelectedRole('ALL')}
              className={`px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap transition-all duration-200 border ${
                selectedRole === 'ALL'
                  ? 'bg-yellow-500 text-black border-yellow-400 shadow-lg font-bold'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border-gray-600 hover:border-gray-500'
              }`}
            >
              {selectedRole === 'ALL' && '✓ '}All Roles
            </button>
            {ROLES.map(role => (
              <button
                key={role}
                onClick={() => setSelectedRole(role)}
                className={`px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap transition-all duration-200 border ${
                  selectedRole === role
                    ? 'bg-yellow-500 text-black border-yellow-400 shadow-lg font-bold'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border-gray-600 hover:border-gray-500'
                }`}
              >
                {selectedRole === role && '✓ '}{role}
              </button>
            ))}
          </div>
          {selectedRole !== 'ALL' && (
            <div className="mt-2 text-xs text-gray-400">
              Active filter: {selectedRole}
            </div>
          )}
        </div>

        {/* Tag Filters */}
        {allTags.length > 0 && (
          <div className="mb-4 ml-4">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium">Tags</label>
              {selectedTags.length > 0 && (
                <button
                  onClick={() => setSelectedTags([])}
                  className="text-xs text-gray-400 hover:text-gray-300 transition-colors"
                >
                  Clear all ({selectedTags.length})
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {allTags.slice(0, 10).map((tag, index) => (
                <button
                  key={`tag-${tag}-${index}`}
                  onClick={() => toggleTag(tag)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-all duration-200 border ${
                    selectedTags.includes(tag)
                      ? 'bg-yellow-500 text-black border-yellow-400 shadow-lg font-bold'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700 border-gray-600 hover:border-gray-500'
                  }`}
                >
                  {selectedTags.includes(tag) && '✓ '}{tag}
                </button>
              ))}
            </div>
            {selectedTags.length > 0 && (
              <div className="mt-2 text-xs text-gray-400">
                Active filters: {selectedTags.join(', ')}
              </div>
            )}
          </div>
        )}

        {/* Results Count */}
        <div className="text-sm text-gray-400 ml-4">
          Showing {filteredChampions.length} of {champions.length} champions
        </div>
      </div>

      {/* Champion Grid */}
      <div className="champion-grid max-h-96 overflow-y-auto pr-2">
        {filteredChampions.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-400">
            No champions found
          </div>
        ) : (
          filteredChampions.map((champion, index) => {
            const disabled = isChampionDisabled(champion);
            return (
              <button
                key={`champ-${champion.id}-${champion.name}-${index}`}
                onClick={() => !disabled && onSelectChampion(champion)}
                className={`champion-card ${disabled ? 'disabled' : ''}`}
                disabled={disabled}
                title={champion.name}
              >
                {/* Champion Image from Data Dragon */}
                <img
                  src={getChampionImageUrl(champion.name)}
                  alt={champion.name}
                  className="absolute inset-0 w-full h-full object-cover"
                  loading="lazy"
                  onError={(e) => {
                    // Log error for debugging
                    console.log(`Failed to load image for ${champion.name}: ${getChampionImageUrl(champion.name)}`);
                    // Fallback to placeholder if image fails to load
                    e.currentTarget.style.display = 'none';
                    e.currentTarget.nextElementSibling?.classList.remove('hidden');
                  }}
                />
                
                {/* Fallback placeholder */}
                <div className="hidden absolute inset-0 flex items-center justify-center bg-gradient-to-br from-gray-700 to-gray-900 text-2xl font-bold text-gray-600">
                  {champion.name.charAt(0)}
                </div>
                
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-2">
                  <div className="text-xs font-semibold text-white text-center truncate drop-shadow-lg">
                    {champion.name}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}

