/**
 * Recommendation Card - Displays champion pick/ban recommendations
 */

import React from 'react';
import { getChampionImageUrl } from '@/lib/championImages';
import type { Champion } from '@/types';

interface ChampionRecommendation {
  champion_id: number;
  champion_name: string;
  win_gain?: number;
  threat_level?: number;
  reasons: string[];
}

interface RecommendationCardProps {
  recommendations: ChampionRecommendation[];
  mode: 'pick' | 'ban';
  role?: string;
  side: 'blue' | 'red';
  champions: Champion[];
  loading?: boolean;
  error?: string;
  onSelect: (_championId: number) => void;
  onClose: () => void;
}

export default function RecommendationCard({
  recommendations,
  mode,
  role,
  side,
  champions,
  loading,
  error,
  onSelect,
  onClose
}: RecommendationCardProps) {
  const getChampionById = (id: number): Champion | undefined => {
    return champions.find(c => parseInt(c.id) === id);
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 animate-fade-in">
        <div className="bg-gray-900 border-2 border-gold-500 rounded-lg p-8 max-w-2xl w-full mx-4">
          <div className="flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-gold-500 mb-4"></div>
            <h3 className="text-xl font-bold text-gold-500">Analyzing Drafts...</h3>
            <p className="text-gray-400 mt-2">
              Evaluating {mode === 'pick' ? 'champion picks' : 'ban threats'} with ML models
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 animate-fade-in">
        <div className="bg-gray-900 border-2 border-red-500 rounded-lg p-8 max-w-2xl w-full mx-4">
          <div className="flex flex-col items-center">
            <div className="text-red-500 text-5xl mb-4">⚠️</div>
            <h3 className="text-xl font-bold text-red-500 mb-2">Recommendation Failed</h3>
            <p className="text-gray-300 text-center mb-6">{error}</p>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 animate-fade-in">
        <div className="bg-gray-900 border-2 border-gold-500 rounded-lg p-8 max-w-2xl w-full mx-4">
          <div className="flex flex-col items-center">
            <div className="text-gray-500 text-5xl mb-4">🤔</div>
            <h3 className="text-xl font-bold text-gold-500 mb-2">No Recommendations Available</h3>
            <p className="text-gray-400 text-center mb-6">
              All champions may be picked or banned. Try a different draft state.
            </p>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gold-600 hover:bg-gold-700 text-black font-bold rounded-lg transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  const sideColor = side === 'blue' ? 'text-blue-400' : 'text-red-400';
  const borderColor = side === 'blue' ? 'border-blue-500' : 'border-red-500';

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 animate-fade-in">
      <div className={`bg-gray-900 border-2 ${borderColor} rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto`}>
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold">
              <span className={sideColor}>{side.toUpperCase()}</span>
              {' '}Smart {mode === 'pick' ? 'Pick' : 'Ban'} Suggestions
            </h2>
            {mode === 'pick' && role && (
              <p className="text-gray-400 mt-1">
                Best {role.toUpperCase()} picks based on current draft
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-3xl leading-none transition"
            title="Close"
          >
            ×
          </button>
        </div>

        {/* Recommendations Grid */}
        <div className="space-y-3">
          {recommendations.map((rec, index) => {
            const champion = getChampionById(rec.champion_id);
            const value = mode === 'pick' ? rec.win_gain : rec.threat_level;
            const valuePercent = value ? Math.abs(value * 100) : 0;
            const barWidth = Math.min(Math.max(valuePercent * 2, 10), 100);
            const _isPositive = value ? value > 0 : false;

            return (
              <div
                key={rec.champion_id}
                className="bg-gray-800 border border-gray-700 hover:border-gold-500 rounded-lg p-4 cursor-pointer transition group"
                onClick={() => onSelect(rec.champion_id)}
              >
                <div className="flex items-center gap-4">
                  {/* Rank Badge */}
                  <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${
                    index === 0 ? 'bg-gold-500 text-black' :
                    index === 1 ? 'bg-gray-400 text-black' :
                    index === 2 ? 'bg-amber-700 text-white' :
                    'bg-gray-700 text-gray-300'
                  }`}>
                    {index + 1}
                  </div>

                  {/* Champion Portrait */}
                  <div className="flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 border-gray-600 group-hover:border-gold-500 transition">
                    {champion ? (
                      <img
                        src={getChampionImageUrl(champion.name)}
                        alt={rec.champion_name}
                        className="w-full h-full object-cover"
                        loading="eager"
                        decoding="async"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          e.currentTarget.nextElementSibling?.classList.remove('hidden');
                        }}
                      />
                    ) : null}
                    <div className="hidden w-full h-full bg-gray-700 flex items-center justify-center text-gray-500">
                      ?
                    </div>
                  </div>

                  {/* Champion Info */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-bold text-white group-hover:text-gold-500 transition truncate">
                      {rec.champion_name}
                    </h3>
                    
                    {/* Win Gain / Threat Bar */}
                    <div className="flex items-center gap-2 mt-1">
                      <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full ${mode === 'pick' ? 'bg-green-500' : 'bg-red-500'} transition-all duration-500`}
                          style={{ width: `${barWidth}%` }}
                        />
                      </div>
                      <span className={`text-sm font-bold ${mode === 'pick' ? 'text-green-400' : 'text-red-400'} min-w-[60px] text-right`}>
                        {mode === 'pick' ? '+' : ''}{valuePercent.toFixed(1)}%
                      </span>
                    </div>

                    {/* Reason Chips */}
                    <div className="flex flex-wrap gap-1 mt-2">
                      {rec.reasons.slice(0, 3).map((reason, i) => (
                        <span
                          key={i}
                          className="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded border border-gray-600"
                        >
                          {reason}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Select Icon */}
                  <div className="flex-shrink-0 text-gray-600 group-hover:text-gold-500 transition text-2xl">
                    →
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-gray-700 flex justify-between items-center">
          <p className="text-sm text-gray-400">
            Click any champion to {mode === 'pick' ? 'select' : 'ban'} it
          </p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white font-bold rounded-lg transition"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

