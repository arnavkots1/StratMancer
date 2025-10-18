'use client';

import { useState, useEffect, useMemo } from 'react';
import { AlertCircle, Loader2, Sparkles } from 'lucide-react';
import ChampionPicker from '@/components/ChampionPicker';
import RoleSlots from '@/components/RoleSlots';
import PredictionCard from '@/components/PredictionCard';
import RecommendationCard from '@/components/RecommendationCard';
import { api } from '@/lib/api';
import type { 
  DraftState, 
  Champion, 
  Elo, 
  PredictionResponse,
  FeatureMap,
  TeamComposition
} from '@/types';

export default function DraftPage() {
  const [draftState, setDraftState] = useState<DraftState>({
    blue: {
      top: null,
      jungle: null,
      mid: null,
      adc: null,
      support: null,
    },
    red: {
      top: null,
      jungle: null,
      mid: null,
      adc: null,
      support: null,
    },
    blueBans: [],
    redBans: [],
    elo: 'mid', // Default to mid (Gold rank) where we have actual data
    patch: undefined,
  });

  // Draft sequence state
  const [draftStep, setDraftStep] = useState<number>(0);
  const [pickTimer, setPickTimer] = useState<number>(30);
  const [timerActive, setTimerActive] = useState<boolean>(false);

  const [champions, setChampions] = useState<Champion[]>([]);
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Recommendation state
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [recommendationError, setRecommendationError] = useState<string | null>(null);

  // Define the draft sequence for Gold rank (with bans)
  // Format: { team, action, role }
  const DRAFT_SEQUENCE = useMemo(() => {
    const sequence: Array<{ team: 'blue' | 'red'; action: 'ban' | 'pick'; role?: keyof TeamComposition }> = [];
    
    // Ban phase (10 bans alternating)
    for (let i = 0; i < 5; i++) {
      sequence.push({ team: 'blue', action: 'ban' });
      sequence.push({ team: 'red', action: 'ban' });
    }
    
    // Pick phase (snake draft)
    const pickOrder: Array<{ team: 'blue' | 'red'; role: keyof TeamComposition }> = [
      { team: 'blue', role: 'top' },
      { team: 'red', role: 'top' },
      { team: 'red', role: 'jungle' },
      { team: 'blue', role: 'jungle' },
      { team: 'blue', role: 'mid' },
      { team: 'red', role: 'mid' },
      { team: 'red', role: 'adc' },
      { team: 'blue', role: 'adc' },
      { team: 'blue', role: 'support' },
      { team: 'red', role: 'support' },
    ];
    
    pickOrder.forEach(pick => {
      sequence.push({ team: pick.team, action: 'pick', role: pick.role });
    });
    
    return sequence;
  }, []);

  const currentDraftAction = useMemo(() => {
    if (draftStep >= DRAFT_SEQUENCE.length) {
      return null; // Draft complete
    }
    return DRAFT_SEQUENCE[draftStep];
  }, [draftStep, DRAFT_SEQUENCE]);

  // Load champion data on mount
  useEffect(() => {
    loadChampions();
  }, []);

  // Pick timer countdown
  useEffect(() => {
    if (!timerActive) return;
    
    if (pickTimer <= 0) {
      setTimerActive(false);
      setPickTimer(30);
      return;
    }

    const interval = setInterval(() => {
      setPickTimer(prev => prev - 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [timerActive, pickTimer]);

  const loadChampions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Try to load feature map from backend
      const featureMap: FeatureMap = await api.getFeatureMap();
      
      // Convert feature map to champion array
      const champArray: Champion[] = Object.entries(featureMap.champ_index).map(([name, index]) => {
        // Find champion ID from id_to_index
        const champId = Object.entries(featureMap.id_to_index).find(
          ([_, idx]) => idx === index
        )?.[0] || '0';
        
        const tags = featureMap.tags[champId] || {};
        
        return {
          id: champId,
          name: name,
          key: champId,
          roles: tags.role || [],
          tags: tags,
        };
      });

      setChampions(champArray);
    } catch (err) {
      console.error('Failed to load champions:', err);
      setError('Failed to load champion data. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  const handlePredictDraft = async () => {
    try {
      setPredicting(true);
      setError(null);

      // Validate draft state - all 5 positions must be filled
      const blueComplete = Object.values(draftState.blue).every(Boolean);
      const redComplete = Object.values(draftState.red).every(Boolean);

      if (!blueComplete || !redComplete) {
        setError('Please complete the draft! All 5 positions must be filled for both teams.');
        return;
      }

      // Convert to API format (backend expects top/jgl/mid/adc/sup keys)
      const requestData = {
        elo: draftState.elo,
        patch: draftState.patch || '15.20',
        blue: {
          top: parseInt(draftState.blue.top!.id),
          jgl: parseInt(draftState.blue.jungle!.id),
          mid: parseInt(draftState.blue.mid!.id),
          adc: parseInt(draftState.blue.adc!.id),
          sup: parseInt(draftState.blue.support!.id),
          bans: draftState.blueBans.map(c => parseInt(c.id)),
        },
        red: {
          top: parseInt(draftState.red.top!.id),
          jgl: parseInt(draftState.red.jungle!.id),
          mid: parseInt(draftState.red.mid!.id),
          adc: parseInt(draftState.red.adc!.id),
          sup: parseInt(draftState.red.support!.id),
          bans: draftState.redBans.map(c => parseInt(c.id)),
        },
      };

      const result = await api.predictDraft(requestData as any);
      setPrediction(result);
    } catch (err: any) {
      console.error('Prediction failed:', err);
      setError(err.message || 'Prediction failed. Please try again.');
    } finally {
      setPredicting(false);
    }
  };

  const handleGetRecommendations = async () => {
    if (!currentDraftAction) return;

    setRecommendationLoading(true);
    setRecommendationError(null);
    setShowRecommendations(true);

    try {
      const { team, action, role } = currentDraftAction;

      // Build draft state for API
      const draftForAPI = {
        elo: draftState.elo,
        side: team,
        blue: {
          top: draftState.blue.top ? parseInt(draftState.blue.top.id) : undefined,
          jungle: draftState.blue.jungle ? parseInt(draftState.blue.jungle.id) : undefined,
          mid: draftState.blue.mid ? parseInt(draftState.blue.mid.id) : undefined,
          adc: draftState.blue.adc ? parseInt(draftState.blue.adc.id) : undefined,
          support: draftState.blue.support ? parseInt(draftState.blue.support.id) : undefined,
          bans: draftState.blueBans.map(c => parseInt(c.id)),
        },
        red: {
          top: draftState.red.top ? parseInt(draftState.red.top.id) : undefined,
          jungle: draftState.red.jungle ? parseInt(draftState.red.jungle.id) : undefined,
          mid: draftState.red.mid ? parseInt(draftState.red.mid.id) : undefined,
          adc: draftState.red.adc ? parseInt(draftState.red.adc.id) : undefined,
          support: draftState.red.support ? parseInt(draftState.red.support.id) : undefined,
          bans: draftState.redBans.map(c => parseInt(c.id)),
        },
        patch: draftState.patch || '15.20',
        top_n: 5,
      };

      let result;
      if (action === 'ban') {
        result = await api.getBanRecommendations(draftForAPI);
      } else if (action === 'pick' && role) {
        result = await api.getPickRecommendations({ ...draftForAPI, role });
      }

      setRecommendations(result);
    } catch (err: any) {
      console.error('Recommendation failed:', err);
      setRecommendationError(err.message || 'Failed to get recommendations');
    } finally {
      setRecommendationLoading(false);
    }
  };

  const handleSelectRecommendation = (championId: number) => {
    const champion = champions.find(c => parseInt(c.id) === championId);
    if (champion) {
      handleChampionSelect(champion);
      setShowRecommendations(false);
      setRecommendations(null);
    }
  };

  const handleResetDraft = () => {
    setDraftState({
      blue: {
        top: null,
        jungle: null,
        mid: null,
        adc: null,
        support: null,
      },
      red: {
        top: null,
        jungle: null,
        mid: null,
        adc: null,
        support: null,
      },
      blueBans: [],
      redBans: [],
      elo: 'mid',
      patch: undefined,
    });
    setPrediction(null);
    setError(null);
    setDraftStep(0);
    setPickTimer(30);
    setTimerActive(false);
    setShowRecommendations(false);
    setRecommendations(null);
  };

  const handleChampionSelect = (champion: Champion) => {
    if (!currentDraftAction) {
      setError('Draft is complete! Click Analyze Draft or Reset.');
      setTimeout(() => setError(null), 3000);
      return;
    }

    const { team, action, role } = currentDraftAction;

    if (action === 'ban') {
      const teamBans = team === 'blue' ? draftState.blueBans : draftState.redBans;
      if (teamBans.length >= 5) {
        setError(`${team.toUpperCase()} team already has 5 bans!`);
        setTimeout(() => setError(null), 3000);
        return;
      }
      if (team === 'blue') {
        setDraftState(prev => ({ ...prev, blueBans: [...prev.blueBans, champion] }));
      } else {
        setDraftState(prev => ({ ...prev, redBans: [...prev.redBans, champion] }));
      }
    } else if (action === 'pick' && role) {
      if (team === 'blue') {
        setDraftState(prev => ({
          ...prev,
          blue: { ...prev.blue, [role]: champion }
        }));
      } else {
        setDraftState(prev => ({
          ...prev,
          red: { ...prev.red, [role]: champion }
        }));
      }
    }

    // Advance to next step
    setDraftStep(prev => prev + 1);
    setPickTimer(30);
    setError(null);
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-16">
        <div className="flex flex-col items-center justify-center space-y-4">
          <Loader2 className="w-12 h-12 text-gold-500 animate-spin" />
          <p className="text-gray-400">Loading champion data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header with Draft Controls */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold mb-2">Draft Analyzer</h1>
              <p className="text-gray-400">
                Click champions to assign them to team positions
              </p>
            </div>
            <div className="flex items-center gap-4">
              {/* Timer */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Pick Timer:</span>
                <div className={`px-4 py-2 rounded-lg font-bold text-xl ${timerActive ? 'bg-red-600 animate-pulse' : 'bg-gray-700'}`}>
                  {pickTimer}s
                </div>
                <button
                  onClick={() => {
                    setTimerActive(!timerActive);
                    if (!timerActive) setPickTimer(30);
                  }}
                  className="btn btn-secondary"
                >
                  {timerActive ? 'Pause' : 'Start'}
                </button>
              </div>
            </div>
          </div>

          {/* Active Draft Step Indicator */}
          {currentDraftAction && (
            <div className={`p-4 border-2 rounded-lg animate-fade-in ${
              currentDraftAction.team === 'blue' 
                ? 'bg-blue-600/10 border-blue-500' 
                : 'bg-red-600/10 border-red-500'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-3xl">
                    {currentDraftAction.action === 'ban' ? '🚫' : '✨'}
                  </div>
                  <div>
                    <div className="font-bold text-xl">
                      <span className={currentDraftAction.team === 'blue' ? 'text-blue-400' : 'text-red-400'}>
                        {currentDraftAction.team.toUpperCase()} TEAM
                      </span>
                      {' - '}
                      {currentDraftAction.action === 'ban' 
                        ? `BAN ${Math.floor((draftStep + 1) / 2)}/5`
                        : `PICK ${currentDraftAction.role?.toUpperCase()}`
                      }
                    </div>
                    <div className="text-sm text-gray-400">
                      Step {draftStep + 1}/{DRAFT_SEQUENCE.length} · Click a champion below
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <button
                    onClick={handleGetRecommendations}
                    disabled={recommendationLoading}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition ${
                      currentDraftAction.team === 'blue'
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-red-600 hover:bg-red-700 text-white'
                    } ${recommendationLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <Sparkles className="w-5 h-5" />
                    {recommendationLoading ? 'Analyzing...' : 'AI Suggest'}
                  </button>
                  <div className="text-right">
                    <div className="text-sm text-gray-400 mb-1">Phase</div>
                    <div className="text-lg font-bold text-gold-500">
                      {currentDraftAction.action === 'ban' ? 'BANNING' : 'PICKING'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {!currentDraftAction && (
            <div className="p-4 bg-green-600/10 border-2 border-green-500 rounded-lg animate-fade-in">
              <div className="flex items-center gap-3">
                <div className="text-3xl">✅</div>
                <div>
                  <div className="font-bold text-xl text-green-400">Draft Complete!</div>
                  <div className="text-sm text-gray-400">Click "Analyze Draft" to see predictions</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/20 border border-red-800 rounded-lg flex items-start space-x-3 animate-fade-in">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-red-400">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-300"
            >
              ×
            </button>
          </div>
        )}

        {/* Game Settings */}
        <div className="card mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium mb-2">
                Rank Tier (Based on Available Data)
              </label>
              <select
                value={draftState.elo}
                onChange={(e) => setDraftState(prev => ({ ...prev, elo: e.target.value as Elo }))}
                className="select"
              >
                <option value="low" disabled>⚪ Iron-Silver (Collect data first)</option>
                <option value="mid">🥇 Gold Rank (100 matches available)</option>
                <option value="high" disabled>👑 Diamond-Challenger (Collect data first)</option>
              </select>
            </div>

            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium mb-2">
                Patch (Optional)
              </label>
              <input
                type="text"
                value={draftState.patch || ''}
                onChange={(e) => setDraftState(prev => ({ ...prev, patch: e.target.value }))}
                placeholder="e.g., 15.20"
                className="input"
              />
            </div>

            <div className="flex items-end space-x-2">
              <button
                onClick={handlePredictDraft}
                disabled={predicting}
                className="btn btn-primary flex items-center space-x-2"
              >
                {predicting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <span>🔮 Analyze Draft</span>
                )}
              </button>

              <button
                onClick={handleResetDraft}
                className="btn btn-secondary"
              >
                🔄 Reset
              </button>
            </div>
          </div>
        </div>

        {/* Team Composition - Read-only Display */}
        <div className="grid lg:grid-cols-2 gap-6 mb-6">
          <div className="card border-2 border-blue-500">
            <div className="mb-4">
              <h2 className="text-xl font-bold text-blue-400">Blue Team</h2>
              <p className="text-sm text-gray-400">
                {currentDraftAction?.team === 'blue' ? '🔴 Currently drafting...' : 'Waiting for turn'}
              </p>
            </div>
            <RoleSlots
              team="blue"
              composition={draftState.blue}
              bans={draftState.blueBans}
              onUpdateComposition={(comp) => setDraftState(prev => ({ ...prev, blue: comp }))}
              onUpdateBans={(bans) => setDraftState(prev => ({ ...prev, blueBans: bans }))}
              currentDraftAction={currentDraftAction}
            />
          </div>

          <div className="card border-2 border-red-500">
            <div className="mb-4">
              <h2 className="text-xl font-bold text-red-400">Red Team</h2>
              <p className="text-sm text-gray-400">
                {currentDraftAction?.team === 'red' ? '🔴 Currently drafting...' : 'Waiting for turn'}
              </p>
            </div>
            <RoleSlots
              team="red"
              composition={draftState.red}
              bans={draftState.redBans}
              onUpdateComposition={(comp) => setDraftState(prev => ({ ...prev, red: comp }))}
              onUpdateBans={(bans) => setDraftState(prev => ({ ...prev, redBans: bans }))}
              currentDraftAction={currentDraftAction}
            />
          </div>
        </div>

        {/* Prediction Results */}
        {prediction && (
          <div className="mb-6">
            <PredictionCard prediction={prediction} />
          </div>
        )}

        {/* Champion Picker */}
        <ChampionPicker
          champions={champions}
          selectedChampions={[
            ...Object.values(draftState.blue).filter(Boolean) as Champion[],
            ...Object.values(draftState.red).filter(Boolean) as Champion[],
          ]}
          bannedChampions={[...draftState.blueBans, ...draftState.redBans]}
          onSelectChampion={handleChampionSelect}
          currentDraftAction={currentDraftAction}
        />

        {/* Recommendation Modal */}
        {showRecommendations && currentDraftAction && (
          <RecommendationCard
            recommendations={recommendations?.recommendations || []}
            mode={currentDraftAction.action === 'ban' ? 'ban' : 'pick'}
            role={currentDraftAction.role}
            side={currentDraftAction.team}
            champions={champions}
            loading={recommendationLoading}
            error={recommendationError || undefined}
            onSelect={handleSelectRecommendation}
            onClose={() => {
              setShowRecommendations(false);
              setRecommendations(null);
              setRecommendationError(null);
            }}
          />
        )}
      </div>
    </div>
  );
}

