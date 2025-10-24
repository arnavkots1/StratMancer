'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { m, AnimatePresence, useReducedMotion } from 'framer-motion';
import { ChevronDown, ChevronUp, Target, Shield, Swords, TrendingUp, Clock, Zap } from 'lucide-react';
import { fadeUp } from '../lib/motion';
import { cn } from '../lib/cn';

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

  const shouldReduceMotion = useReducedMotion();
  const [typedSummary, setTypedSummary] = useState('');
  const summaryLine = useMemo(() => {
    return (
      analysis.game_plan?.early_game?.[0] ??
      'Secure early objective control and leverage draft win conditions.'
    );
  }, [analysis]);

  useEffect(() => {
    if (shouldReduceMotion) {
      setTypedSummary(summaryLine);
      return;
    }
    setTypedSummary('');
    let frame = 0;
    const interval = window.setInterval(() => {
      frame += 1;
      setTypedSummary(summaryLine.slice(0, frame));
      if (frame >= summaryLine.length) {
        window.clearInterval(interval);
      }
    }, 24);

    return () => window.clearInterval(interval);
  }, [summaryLine, shouldReduceMotion]);

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const favoredTeam = analysis.summary.favored_team;
  const confidence = (analysis.summary.confidence * 100).toFixed(0);

  return (
    <m.section
      initial={{ opacity: 0.85, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 16 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="relative overflow-hidden rounded-[28px] border border-white/10 bg-[#0d1424]/85 p-6 backdrop-blur-xl"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(124,58,237,0.2),transparent_60%)] opacity-70" />
      <div className="relative space-y-6">
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
      <m.div
        variants={fadeUp}
        className="rounded-2xl border border-white/10 bg-black/30 p-4"
      >
        <button
          className="flex w-full items-center justify-between text-left"
          onClick={() => toggleSection('summary')}
        >
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Target className="h-5 w-5 text-accent" />
            Overview
          </div>
          {expandedSections.summary ? (
            <ChevronUp className="h-5 w-5 text-white/60" />
          ) : (
            <ChevronDown className="h-5 w-5 text-white/60" />
          )}
        </button>

        <AnimatePresence initial={false}>
          {expandedSections.summary && (
            <m.div
              key="summary-content"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
              className="mt-4 space-y-4"
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-xl border border-white/10 bg-[#10172a]/80 p-4">
                  <div className="text-xs uppercase tracking-[0.28em] text-white/40">Blue Team</div>
                  <div className="mt-2 text-2xl font-semibold text-sky-300">
                    {(analysis.summary.blue_win_probability * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="rounded-xl border border-white/10 bg-[#10172a]/80 p-4 text-right">
                  <div className="text-xs uppercase tracking-[0.28em] text-white/40">Red Team</div>
                  <div className="mt-2 text-2xl font-semibold text-rose-300">
                    {(analysis.summary.red_win_probability * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-[#10172a]/80 p-4">
                <div className="text-xs uppercase tracking-[0.28em] text-white/40">AI Summary</div>
                <p className="mt-3 font-mono text-sm text-white/70">
                  {typedSummary}
                  {!shouldReduceMotion && <span className="ml-1 animate-pulse text-accent">▌</span>}
                </p>
              </div>

              <div className="rounded-xl border border-white/10 bg-[#10172a]/80 p-4">
                <div className="text-xs uppercase tracking-[0.28em] text-white/40">Prediction</div>
                <div className="mt-2 text-lg font-semibold text-white">
                  <span className={favoredTeam === 'blue' ? 'text-sky-300' : 'text-rose-300'}>
                    {favoredTeam.toUpperCase()} TEAM
                  </span>{' '}
                  favored ({confidence}% confidence)
                </div>
              </div>
            </m.div>
          )}
        </AnimatePresence>
      </m.div>

      {/* Lane Matchups */}
      <m.div variants={fadeUp} className="rounded-2xl border border-white/10 bg-black/30 p-4">
        <button
          className="flex w-full items-center justify-between text-left"
          onClick={() => toggleSection('matchups')}
        >
          <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
            <Swords className="h-5 w-5 text-accent" />
            Lane Matchups
          </h3>
          {expandedSections.matchups ? (
            <ChevronUp className="h-5 w-5 text-white/60" />
          ) : (
            <ChevronDown className="h-5 w-5 text-white/60" />
          )}
        </button>
        
        {expandedSections.matchups && (
          <div className="mt-4 space-y-3">
            {analysis.matchups.map((matchup, idx) => (
              <div key={idx} className="rounded-xl border border-white/10 bg-[#10172a]/80 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-xs uppercase tracking-[0.28em] text-white/40">{matchup.lane}</span>
                  <span
                    className={cn(
                      'rounded-full px-3 py-1 text-[10px] uppercase tracking-[0.28em]',
                      matchup.advantage === 'blue'
                        ? 'border border-sky-400/40 bg-sky-500/10 text-sky-200'
                        : matchup.advantage === 'red'
                        ? 'border border-rose-400/40 bg-rose-500/10 text-rose-200'
                        : 'border border-white/10 bg-black/20 text-white/60',
                    )}
                  >
                    {matchup.advantage === 'even' ? 'Even' : `${matchup.advantage.toUpperCase()} Advantage`}
                  </span>
                </div>
                <div className="mb-1 text-sm font-semibold text-white">
                  {matchup.blue_champion} vs {matchup.red_champion}
                </div>
                <div className="mb-2 text-xs text-white/60">{matchup.note}</div>
                <div className="space-y-1">
                  {matchup.tips.map((tip, tipIdx) => (
                    <div key={tipIdx} className="flex items-start gap-2 text-xs text-white/55">
                      <span className="text-accent">•</span>
                      <span>{tip}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </m.div>

      {/* Blue Team Analysis */}
      <m.div variants={fadeUp} className="rounded-2xl border border-white/10 bg-black/30 p-4">
        <button
          className="flex w-full items-center justify-between text-left"
          onClick={() => toggleSection('blueTeam')}
        >
          <h3 className="flex items-center gap-2 text-sm font-semibold text-sky-300">
            <Shield className="h-5 w-5" />
            Blue Team Strategy
          </h3>
          {expandedSections.blueTeam ? (
            <ChevronUp className="h-5 w-5 text-white/60" />
          ) : (
            <ChevronDown className="h-5 w-5 text-white/60" />
          )}
        </button>
        
        {expandedSections.blueTeam && (
          <m.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="mt-4 space-y-4"
          >
            <TeamAnalysis team={analysis.blue_team} color="blue" />
          </m.div>
        )}
      </m.div>

      {/* Red Team Analysis */}
      <m.div variants={fadeUp} className="rounded-2xl border border-white/10 bg-black/30 p-4">
        <button
          className="flex w-full items-center justify-between text-left"
          onClick={() => toggleSection('redTeam')}
        >
          <h3 className="flex items-center gap-2 text-sm font-semibold text-rose-300">
            <Shield className="h-5 w-5" />
            Red Team Strategy
          </h3>
          {expandedSections.redTeam ? (
            <ChevronUp className="h-5 w-5 text-white/60" />
          ) : (
            <ChevronDown className="h-5 w-5 text-white/60" />
          )}
        </button>

        {expandedSections.redTeam && (
          <m.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="mt-4 space-y-4"
          >
            <TeamAnalysis team={analysis.red_team} color="red" />
          </m.div>
        )}
      </m.div>

      {/* Game Plan */}
      <m.div variants={fadeUp} className="rounded-2xl border border-white/10 bg-black/30 p-4">
        <button
          className="flex w-full items-center justify-between text-left"
          onClick={() => toggleSection('gamePlan')}
        >
          <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
            <Clock className="h-5 w-5 text-accent" />
            Game Plan
          </h3>
          {expandedSections.gamePlan ? (
            <ChevronUp className="h-5 w-5 text-white/60" />
          ) : (
            <ChevronDown className="h-5 w-5 text-white/60" />
          )}
        </button>
        
        {expandedSections.gamePlan && (
          <m.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="mt-4 grid gap-4 md:grid-cols-3"
          >
            <GamePhase phase="Early Game" items={analysis.game_plan.early_game} />
            <GamePhase phase="Mid Game" items={analysis.game_plan.mid_game} />
            <GamePhase phase="Late Game" items={analysis.game_plan.late_game} />
          </m.div>
        )}
      </m.div>
      </div>
    </m.section>
  );
}

function TeamAnalysis({ team, color }: { team: any; color: 'blue' | 'red' }) {
  const accentClass = color === 'blue' ? 'text-sky-300' : 'text-rose-300'

  return (
    <div className="space-y-3">
      {/* Composition Type */}
      <div className="rounded-xl border border-white/10 bg-[#10172a]/80 p-4">
        <div className="mb-2 text-xs uppercase tracking-[0.28em] text-white/40">Composition Type</div>
        <div className="text-sm font-semibold text-white/80">{team.composition.type}</div>
      </div>

      {/* Win Conditions */}
      <div className="rounded-xl border border-white/10 bg-[#10172a]/80 p-4">
        <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.28em] text-white/40">
          <Target className="h-4 w-4 text-accent" />
          Win Conditions
        </div>
        <ul className="space-y-1">
          {team.win_conditions.map((condition: string, idx: number) => (
            <li key={idx} className="flex items-start gap-2 text-sm text-white/70">
              <span className="mt-1 text-accent">→</span>
              <span>{condition}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Key Threats */}
      {team.key_threats.length > 0 && (
        <div className="rounded-xl border border-white/10 bg-[#10172a]/80 p-4">
          <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.28em] text-white/40">
            <Shield className="h-4 w-4 text-accent" />
            Key Threats to Watch
          </div>
          <div className="space-y-2">
            {team.key_threats.map((threat: any, idx: number) => (
              <div key={idx} className="text-sm text-white/70">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white/85">{threat.champion}</span>
                  <span className={cn(
                    'rounded-full px-2 py-1 text-[11px] uppercase tracking-[0.24em]',
                    threat.threat_level === 'High'
                      ? 'border border-rose-400/40 bg-rose-500/10 text-rose-200'
                      : 'border border-amber-400/40 bg-amber-500/10 text-amber-200',
                  )}>
                    {threat.threat_level}
                  </span>
                </div>
                <div className="text-xs text-white/50">{threat.reason}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Power Spikes */}
      <div className="rounded-xl border border-white/10 bg-[#10172a]/80 p-4">
        <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.28em] text-white/40">
          <TrendingUp className={cn('h-4 w-4', accentClass)} />
          Power Spikes
        </div>
        <div className="space-y-2 text-xs text-white/60">
          {Object.entries(team.power_spikes).map(([phase, champs]: [string, any]) => (
            champs.length > 0 && (
              <div key={phase}>
                <div className="font-semibold uppercase tracking-[0.24em] text-white/45">{phase.replace('_', ' ')}</div>
                <ul className="ml-4 space-y-1 text-white/70">
                  {champs.map((champ: string, idx: number) => (
                    <li key={idx}>{champ}</li>
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
    <div className="rounded-xl border border-white/10 bg-[#10172a]/80 p-4">
      <div className="mb-2 text-xs uppercase tracking-[0.28em] text-white/40">{phase}</div>
      <ul className="space-y-2 text-sm text-white/70">
        {items.map((item, idx) => (
          <li key={idx} className="flex items-start gap-2">
            <span className="text-accent">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

