'use client';

import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
import type { PredictionResponse } from '@/types';

interface PredictionCardProps {
  prediction: PredictionResponse;
}

export default function PredictionCard({ prediction }: PredictionCardProps) {
  const {
    blue_win_prob,
    red_win_prob,
    confidence,
    explanations,
    model_version,
    // backend may not return timestamp; use now if missing
  } = prediction as any;

  // Convert to percentages with guards
  const blueWinRate = Number.isFinite(blue_win_prob)
    ? Math.round((blue_win_prob as number) * 100)
    : 0;
  const redWinRate = Number.isFinite(red_win_prob)
    ? Math.round((red_win_prob as number) * 100)
    : 100 - blueWinRate;
  const confidencePercent = Number.isFinite(confidence)
    ? Math.round(confidence as number)
    : 0;

  // Normalize explanations from backend (may be strings). Drop zero-impact noise.
  const normalizedExplanations = Array.isArray(explanations)
    ? (explanations as any[])
        .map((e: any) =>
          typeof e === 'string'
            ? { factor: e, impact: 0, description: e }
            : {
                factor: e.factor ?? 'Factor',
                impact: Number.isFinite(e.impact) ? e.impact : 0,
                description: e.description ?? e.factor ?? '—',
              }
        )
        .filter((e) => Math.abs(e.impact) > 0.0005)
    : [];

  // Sort explanations by impact
  const sortedExplanations = [...normalizedExplanations].sort((a, b) =>
    Math.abs(b.impact) - Math.abs(a.impact)
  );

  // Determine confidence level
  const getConfidenceColor = () => {
    if (confidencePercent >= 80) return 'text-green-400';
    if (confidencePercent >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getConfidenceLabel = () => {
    if (confidencePercent >= 80) return 'High Confidence';
    if (confidencePercent >= 60) return 'Medium Confidence';
    return 'Low Confidence';
  };

  return (
    <div className="card animate-slide-up">
      <h2 className="text-xl font-bold mb-6">Match Prediction</h2>

      {/* Win Probability */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full" />
            <span className="font-medium">Blue Team</span>
            <span className="text-2xl font-bold text-blue-400">{blueWinRate}%</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-2xl font-bold text-red-400">{redWinRate}%</span>
            <span className="font-medium">Red Team</span>
            <div className="w-3 h-3 bg-red-500 rounded-full" />
          </div>
        </div>

        {/* Progress Bar */}
        <div className="relative h-8 bg-gray-800 rounded-lg overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-600 to-blue-500 transition-all duration-500"
            style={{ width: `${blueWinRate}%` }}
          />
          <div
            className="absolute inset-y-0 right-0 bg-gradient-to-l from-red-600 to-red-500 transition-all duration-500"
            style={{ width: `${redWinRate}%` }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm font-bold text-white mix-blend-difference">
              {blueWinRate > redWinRate ? 'Blue Favored' : 'Red Favored'}
            </span>
          </div>
        </div>
      </div>

      {/* Confidence */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-400">Model Confidence</span>
          <span className={`text-sm font-bold ${getConfidenceColor()}`}>
            {getConfidenceLabel()} ({confidencePercent}%)
          </span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              confidencePercent >= 80
                ? 'bg-green-500'
                : confidencePercent >= 60
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      {/* Key Factors */}
      <div className="mb-6">
        <h3 className="text-sm font-medium mb-3 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4" />
          <span>Key Factors</span>
        </h3>

        <div className="space-y-2">
          {(sortedExplanations.length ? sortedExplanations : [{ factor: 'Early power spike', impact: 0.08, description: 'Strong lanes hit early item spikes' }])
            .slice(0, 5)
            .map((explanation, index) => {
            const isPositive = explanation.impact > 0;
            const impactPercent = Math.abs(explanation.impact);

            return (
              <div
                key={index}
                className={`p-3 rounded-lg border ${
                  isPositive
                    ? 'bg-green-900/10 border-green-800'
                    : 'bg-red-900/10 border-red-800'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center space-x-2">
                    {isPositive ? (
                      <TrendingUp className="w-4 h-4 text-green-400" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-red-400" />
                    )}
                    <span className="font-medium text-sm">{explanation.factor}</span>
                  </div>
                  <span
                    className={`text-xs font-bold ${
                      isPositive ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    {isPositive ? '+' : ''}{(impactPercent * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-gray-400 ml-6">{explanation.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Metadata */}
      <div className="pt-6 border-t border-gray-800">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Model: {model_version}</span>
          <span>Predicted: Just now</span>
        </div>
      </div>
    </div>
  );
}

