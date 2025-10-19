'use client';

import React from 'react';
import { ChevronDown, ChevronUp, Target, Shield, Swords, TrendingUp, Clock, Zap } from 'lucide-react';

interface AnalysisData {
  summary: {
    blue_win_probability: number;
    red_win_probability: number;
    favored_team: string;
    confidence: number;
    elo_group: string;
    patch: string;
  };
  blue_team: {
    composition: any;
    win_conditions: string[];
    key_threats: Array<{champion: string; role: string; threat_level: string; reason: string}>;
    power_spikes: {early: string[]; mid: string[]; late: string[]};
    champions: any;
  };
  red_team: {
    composition: any;
    win_conditions: string[];
    key_threats: Array<{champion: string; role: string; threat_level: string; reason: string}>;
    power_spikes: {early: string[]; mid: string[]; late: string[]};
    champions: any;
  };
  matchups: Array<{
    lane: string;
    blue_champion: string;
    red_champion: string;
    advantage: string;
    note: string;
    tips: string[];
  }>;
  game_plan: {
    early_game: string[];
    mid_game: string[];
    late_game: string[];
  };
}

interface AnalysisPanelProps {
  analysis: AnalysisData;
  onClose?: () => void;
}

export default function AnalysisPanel({ analysis, onClose }: AnalysisPanelProps) {
  const [expandedSections, setExpandedSections] = React.useState({
    summary: true,
    matchups: true,
    blueTeam: false,
    redTeam: false,
    gamePlan: false,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const favoredTeam = analysis.summary.favored_team;
  const confidence = (analysis.summary.confidence * 100).toFixed(0);

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gold-500 flex items-center gap-2">
          <Zap className="w-6 h-6" />
          Draft Analysis
        </h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ×
          </button>
        )}
      </div>

      {/* Summary Section */}
      <div className="bg-gray-900 rounded-lg p-4">
        <button
          className="w-full flex items-center justify-between"
          onClick={() => toggleSection('summary')}
        >
          <h3 className="text-xl font-semibold text-white flex items-center gap-2">
            <Target className="w-5 h-5 text-gold-500" />
            Overview
          </h3>
          {expandedSections.summary ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
        
        {expandedSections.summary && (
          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-900/30 border border-blue-500/50 rounded p-3">
                <div className="text-sm text-gray-400">Blue Team</div>
                <div className="text-2xl font-bold text-blue-400">
                  {(analysis.summary.blue_win_probability * 100).toFixed(1)}%
                </div>
              </div>
              <div className="bg-red-900/30 border border-red-500/50 rounded p-3">
                <div className="text-sm text-gray-400">Red Team</div>
                <div className="text-2xl font-bold text-red-400">
                  {(analysis.summary.red_win_probability * 100).toFixed(1)}%
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 rounded p-3">
              <div className="text-sm text-gray-400">Prediction</div>
              <div className="text-lg font-semibold">
                <span className={favoredTeam === 'blue' ? 'text-blue-400' : 'text-red-400'}>
                  {favoredTeam.toUpperCase()} TEAM
                </span>
                {' '}favored ({confidence}% confidence)
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Lane Matchups */}
      <div className="bg-gray-900 rounded-lg p-4">
        <button
          className="w-full flex items-center justify-between"
          onClick={() => toggleSection('matchups')}
        >
          <h3 className="text-xl font-semibold text-white flex items-center gap-2">
            <Swords className="w-5 h-5 text-gold-500" />
            Lane Matchups
          </h3>
          {expandedSections.matchups ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
        
        {expandedSections.matchups && (
          <div className="mt-4 space-y-3">
            {analysis.matchups.map((matchup, idx) => (
              <div key={idx} className="bg-gray-800 rounded p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-gray-400">{matchup.lane}</span>
                  <span className={`text-xs px-2 py-1 rounded ${
                    matchup.advantage === 'blue' ? 'bg-blue-900/50 text-blue-400' :
                    matchup.advantage === 'red' ? 'bg-red-900/50 text-red-400' :
                    'bg-gray-700 text-gray-400'
                  }`}>
                    {matchup.advantage === 'even' ? 'Even' : `${matchup.advantage.toUpperCase()} Advantage`}
                  </span>
                </div>
                <div className="text-white font-medium mb-1">
                  {matchup.blue_champion} vs {matchup.red_champion}
                </div>
                <div className="text-sm text-gray-400 mb-2">{matchup.note}</div>
                <div className="space-y-1">
                  {matchup.tips.map((tip, tipIdx) => (
                    <div key={tipIdx} className="text-xs text-gray-500 flex items-start gap-1">
                      <span className="text-gold-500">•</span>
                      <span>{tip}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Blue Team Analysis */}
      <div className="bg-gray-900 rounded-lg p-4">
        <button
          className="w-full flex items-center justify-between"
          onClick={() => toggleSection('blueTeam')}
        >
          <h3 className="text-xl font-semibold text-blue-400 flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Blue Team Strategy
          </h3>
          {expandedSections.blueTeam ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
        
        {expandedSections.blueTeam && (
          <div className="mt-4 space-y-4">
            <TeamAnalysis team={analysis.blue_team} color="blue" />
          </div>
        )}
      </div>

      {/* Red Team Analysis */}
      <div className="bg-gray-900 rounded-lg p-4">
        <button
          className="w-full flex items-center justify-between"
          onClick={() => toggleSection('redTeam')}
        >
          <h3 className="text-xl font-semibold text-red-400 flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Red Team Strategy
          </h3>
          {expandedSections.redTeam ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
        
        {expandedSections.redTeam && (
          <div className="mt-4 space-y-4">
            <TeamAnalysis team={analysis.red_team} color="red" />
          </div>
        )}
      </div>

      {/* Game Plan */}
      <div className="bg-gray-900 rounded-lg p-4">
        <button
          className="w-full flex items-center justify-between"
          onClick={() => toggleSection('gamePlan')}
        >
          <h3 className="text-xl font-semibold text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-gold-500" />
            Game Plan
          </h3>
          {expandedSections.gamePlan ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
        
        {expandedSections.gamePlan && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <GamePhase phase="Early Game" items={analysis.game_plan.early_game} />
            <GamePhase phase="Mid Game" items={analysis.game_plan.mid_game} />
            <GamePhase phase="Late Game" items={analysis.game_plan.late_game} />
          </div>
        )}
      </div>
    </div>
  );
}

function TeamAnalysis({ team, color }: { team: any; color: 'blue' | 'red' }) {
  return (
    <div className="space-y-3">
      {/* Composition Type */}
      <div className="bg-gray-800 rounded p-3">
        <div className="text-sm text-gray-400 mb-1">Composition Type</div>
        <div className="text-white font-semibold">{team.composition.type}</div>
      </div>

      {/* Win Conditions */}
      <div className="bg-gray-800 rounded p-3">
        <div className="text-sm text-gray-400 mb-2 flex items-center gap-1">
          <Target className="w-4 h-4" />
          Win Conditions
        </div>
        <ul className="space-y-1">
          {team.win_conditions.map((condition: string, idx: number) => (
            <li key={idx} className="text-sm text-white flex items-start gap-2">
              <span className="text-gold-500 mt-1">→</span>
              <span>{condition}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Key Threats */}
      {team.key_threats.length > 0 && (
        <div className="bg-gray-800 rounded p-3">
          <div className="text-sm text-gray-400 mb-2 flex items-center gap-1">
            <Shield className="w-4 h-4" />
            Key Threats to Watch
          </div>
          <div className="space-y-2">
            {team.key_threats.map((threat: any, idx: number) => (
              <div key={idx} className="text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-white font-medium">{threat.champion}</span>
                  <span className={`text-xs px-2 py-1 rounded ${
                    threat.threat_level === 'High' ? 'bg-red-900/50 text-red-400' : 'bg-yellow-900/50 text-yellow-400'
                  }`}>
                    {threat.threat_level}
                  </span>
                </div>
                <div className="text-xs text-gray-500">{threat.reason}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Power Spikes */}
      <div className="bg-gray-800 rounded p-3">
        <div className="text-sm text-gray-400 mb-2 flex items-center gap-1">
          <TrendingUp className="w-4 h-4" />
          Power Spikes
        </div>
        <div className="space-y-2 text-xs">
          {Object.entries(team.power_spikes).map(([phase, champs]: [string, any]) => (
            champs.length > 0 && (
              <div key={phase}>
                <div className="text-gray-400 font-semibold capitalize">{phase.replace('_', ' ')}</div>
                <ul className="ml-4 space-y-1">
                  {champs.map((champ: string, idx: number) => (
                    <li key={idx} className="text-gray-300">{champ}</li>
                  ))}
                </ul>
              </div>
            )
          ))}
        </div>
      </div>
    </div>
  );
}

function GamePhase({ phase, items }: { phase: string; items: string[] }) {
  return (
    <div className="bg-gray-800 rounded p-3">
      <div className="text-sm font-semibold text-gold-500 mb-2">{phase}</div>
      <ul className="space-y-2">
        {items.map((item, idx) => (
          <li key={idx} className="text-xs text-gray-300 flex items-start gap-1">
            <span className="text-gold-500">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

