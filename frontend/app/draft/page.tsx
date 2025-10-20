'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { AlertCircle, Loader2, Sparkles } from 'lucide-react';
import ChampionPicker from '@/components/ChampionPicker';
import RoleSlots from '@/components/RoleSlots';
import PredictionCard from '@/components/PredictionCard';
import RecommendationCard from '@/components/RecommendationCard';
import AnalysisPanel from '@/components/AnalysisPanel';
import { api } from '@/lib/api';
import { getChampionImageUrl } from '@/lib/championImages';
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

  // Analysis state
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);
  // Require explicit start to begin any draft interactions
  const [draftStarted, setDraftStarted] = useState<boolean>(false);

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
      const champArray: Champion[] = Object.entries(featureMap.champ_index).map(([name, championId]) => {
        // Values in champ_index are the actual Riot champion IDs
        const champId = String(championId);
        const tags = featureMap.tags[champId] || {};
        
        // Convert role string to array and normalize to uppercase
        let roleArray: string[] = [];
        if (tags.role) {
          if (Array.isArray(tags.role)) {
            roleArray = tags.role;
          } else if (typeof tags.role === 'string') {
            roleArray = [tags.role];
          }
        }
        
        return {
          id: champId, // This is the actual champion ID (e.g., "67" for Vayne)
          name: name,
          key: champId,
          roles: roleArray.map((r: string) => r.toUpperCase()) as any,
          tags: tags,
        };
      });

      console.log('Loaded champions:', champArray.length);
      console.log('First few champions:', champArray.slice(0, 5));
      setChampions(champArray);
    } catch (err) {
      console.error('Failed to load champions:', err);
      setError('Failed to load champion data. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  const handlePredictDraft = async () => {
    if (!draftStarted) {
      setError('Click "Start Draft" to begin.');
      return;
    }
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
      
      // Automatically trigger analysis after prediction
      handleAnalyzeDraft(requestData, result);
    } catch (err: any) {
      console.error('Prediction failed:', err);
      setError(err.message || 'Prediction failed. Please try again.');
    } finally {
      setPredicting(false);
    }
  };

  const handleAnalyzeDraft = async (draftData: any, predictionResult: PredictionResponse) => {
    try {
      setAnalyzing(true);
      
      const analysisData = {
        ...draftData,
        blue_win_prob: predictionResult.blue_win_prob,
        red_win_prob: predictionResult.red_win_prob,
      };

      const result = await api.analyzeDraft(analysisData);
      setAnalysis(result);
      setShowAnalysis(true);
    } catch (err: any) {
      console.error('Analysis failed:', err);
      // Don't show error to user - analysis is optional
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGetRecommendations = useCallback(async () => {
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
          jgl: draftState.blue.jungle ? parseInt(draftState.blue.jungle.id) : undefined,
          mid: draftState.blue.mid ? parseInt(draftState.blue.mid.id) : undefined,
          adc: draftState.blue.adc ? parseInt(draftState.blue.adc.id) : undefined,
          sup: draftState.blue.support ? parseInt(draftState.blue.support.id) : undefined,
          bans: draftState.blueBans.map(c => parseInt(c.id)),
        },
        red: {
          top: draftState.red.top ? parseInt(draftState.red.top.id) : undefined,
          jgl: draftState.red.jungle ? parseInt(draftState.red.jungle.id) : undefined,
          mid: draftState.red.mid ? parseInt(draftState.red.mid.id) : undefined,
          adc: draftState.red.adc ? parseInt(draftState.red.adc.id) : undefined,
          sup: draftState.red.support ? parseInt(draftState.red.support.id) : undefined,
          bans: draftState.redBans.map(c => parseInt(c.id)),
        },
        patch: draftState.patch || '15.20',
        top_n: 5,
      };

      // Debug logging
      console.log('Frontend ban data being sent:');
      console.log('Blue bans:', draftState.blueBans.map(c => `${c.name} (ID: ${c.id})`));
      console.log('Red bans:', draftState.redBans.map(c => `${c.name} (ID: ${c.id})`));
      console.log('Blue ban IDs:', draftForAPI.blue.bans);
      console.log('Red ban IDs:', draftForAPI.red.bans);
      
      // Check specifically for Vayne
      const vayneInBlue = draftState.blueBans.find(c => c.name === 'Vayne');
      const vayneInRed = draftState.redBans.find(c => c.name === 'Vayne');
      if (vayneInBlue) console.log('Vayne in blue bans:', vayneInBlue.id);
      if (vayneInRed) console.log('Vayne in red bans:', vayneInRed.id);

      let result;
      if (action === 'ban') {
        result = await api.getBanRecommendations(draftForAPI);
      } else if (action === 'pick' && role) {
        // Map frontend role names to backend role names
        const roleMap: Record<string, 'top' | 'jgl' | 'mid' | 'adc' | 'sup'> = {
          'jungle': 'jgl',
          'support': 'sup',
          'top': 'top',
          'mid': 'mid',
          'adc': 'adc'
        };
        const backendRole = roleMap[role] || role as 'top' | 'jgl' | 'mid' | 'adc' | 'sup';
        result = await api.getPickRecommendations({ ...draftForAPI, role: backendRole });
      }

      setRecommendations(result);
    } catch (err: any) {
      console.error('Recommendation failed:', err);
      setRecommendationError(err.message || 'Failed to get recommendations');
    } finally {
      setRecommendationLoading(false);
    }
  }, [currentDraftAction, draftState, api]);

  // Auto-show recommendations when draft step changes (only after draft starts)
  useEffect(() => {
    if (currentDraftAction && champions.length > 0 && draftStep > 0) {
      // Auto-get recommendations for each new draft step (only after draft has started)
      handleGetRecommendations();
    }
  }, [currentDraftAction, draftStep, champions.length, handleGetRecommendations]);

  const handleSelectRecommendation = (championId: number) => {
    console.log('Selecting recommendation:', championId);
    console.log('Available champions:', champions.length);
    const champion = champions.find(c => parseInt(c.id) === championId);
    console.log('Found champion:', champion);
    if (champion) {
      handleChampionSelect(champion);
      setShowRecommendations(false);
      setRecommendations(null);
    } else {
      console.error('Champion not found for ID:', championId);
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
    setShowAnalysis(false);
    setAnalysis(null);
  };

  const handleChampionSelect = (champion: Champion) => {
    if (!draftStarted) {
      setError('Click "Start Draft" to begin.');
      setTimeout(() => setError(null), 2000);
      return;
    }
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
              {/* Start Draft */}
              <button
                className={`btn ${draftStarted ? 'btn-secondary' : 'btn-primary'}`}
                onClick={() => setDraftStarted(true)}
                disabled={draftStarted}
                title={draftStarted ? 'Draft already started' : 'Start Draft'}
              >
                {draftStarted ? 'Draft Started' : 'Start Draft'}
              </button>
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
                <div className="text-right">
                  <div className="text-sm text-gray-400 mb-1">Phase</div>
                  <div className="text-lg font-bold text-gold-500">
                    {currentDraftAction.action === 'ban' ? 'BANNING' : 'PICKING'}
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

        {/* Team Composition and AI Recommendations - Same Row */}
        <div className="grid lg:grid-cols-3 gap-6 mb-6">
          {/* Blue Team */}
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

          {/* Red Team */}
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

          {/* AI Recommendations */}
          {currentDraftAction && (
            <div className="card border-2 border-gold-500">
              <div className="mb-4">
                <h2 className="text-xl font-bold text-gold-500 mb-2">🤖 AI Recommendations</h2>
                <p className="text-sm text-gray-400">
                  Get smart suggestions for {currentDraftAction.action === 'ban' ? 'bans' : 'picks'} based on current draft state
                </p>
              </div>
              
              <div className="flex flex-col gap-2">
                {recommendationLoading && (
                  <div className="flex items-center justify-center gap-2 text-gold-500">
                    <Sparkles className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Analyzing...</span>
                  </div>
                )}
                
                {recommendations && !recommendationLoading && (
                  <div className="text-sm text-gray-400 text-center">
                    Found {recommendations.recommendations?.length || 0} recommendations
                  </div>
                )}
              </div>

              {/* Show recommendations inline */}
              {recommendations && recommendations.recommendations && (
                <div className="mt-4 space-y-2">
                  {recommendations.recommendations.slice(0, 5).map((rec: any, index: number) => {
                    // Find champion by ID (try both string and number comparison)
                    const champion = champions.find(c => 
                      c.id === rec.champion_id.toString() || 
                      parseInt(c.id) === rec.champion_id ||
                      c.name === rec.champion_name
                    );
                    
                    // Check if champion is already picked (client-side verification)
                    const isAlreadyPicked = 
                      Object.values(draftState.blue).some((c: any) => c && parseInt(c.id) === rec.champion_id) ||
                      Object.values(draftState.red).some((c: any) => c && parseInt(c.id) === rec.champion_id);
                    
                    // Check if champion is banned (client-side verification)
                    const isBanned = 
                      draftState.blueBans.some((c: any) => parseInt(c.id) === rec.champion_id) ||
                      draftState.redBans.some((c: any) => parseInt(c.id) === rec.champion_id);
                    
                    // Skip this recommendation if champion is already picked or banned
                    if (isAlreadyPicked || isBanned) {
                      return null;
                    }
                    const value = currentDraftAction.action === 'ban' ? rec.threat_level : rec.win_gain;
                    const valuePercent = value ? Math.abs(value * 100) : 0;
                    const barWidth = Math.min(Math.max(valuePercent * 3, 5), 100);

                    return (
                      <div
                        key={rec.champion_id}
                        className="bg-gray-800 border border-gray-700 hover:border-gold-500 rounded-lg p-2 cursor-pointer transition group"
                        onClick={() => {
                          if (champion) {
                            handleChampionSelect(champion);
                            setShowRecommendations(false);
                            setRecommendations(null);
                          }
                        }}
                      >
                        <div className="flex items-center gap-2">
                          {/* Rank Badge */}
                          <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                            index === 0 ? 'bg-gold-500 text-black' :
                            index === 1 ? 'bg-gray-400 text-black' :
                            index === 2 ? 'bg-amber-700 text-white' :
                            'bg-gray-700 text-gray-300'
                          }`}>
                            {index + 1}
                          </div>

                          {/* Champion Portrait */}
                          <div className="flex-shrink-0 w-8 h-8 rounded-lg overflow-hidden border border-gray-600 group-hover:border-gold-500 transition">
                            <img
                              src={getChampionImageUrl(champion?.name || rec.champion_name)}
                              alt={rec.champion_name}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                console.log('Image failed for:', rec.champion_name, 'Champion found:', !!champion);
                                e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiBmaWxsPSIjMzc0MTUxIi8+Cjx0ZXh0IHg9IjE2IiB5PSIyMCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiBmaWxsPSIjOUI5QjlCIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj4/CjwvdGV4dD4KPC9zdmc+';
                              }}
                            />
                          </div>

                          {/* Champion Info */}
                          <div className="flex-1 min-w-0">
                            <h4 className="text-xs font-bold text-white group-hover:text-gold-500 transition truncate">
                              {rec.champion_name}
                            </h4>
                            
                            {/* Value Bar */}
                            <div className="flex items-center gap-1 mt-1">
                              <div className="flex-1 bg-gray-700 rounded-full h-1 overflow-hidden">
                                <div
                                  className={`h-full ${currentDraftAction.action === 'ban' ? 'bg-red-500' : 'bg-green-500'} transition-all duration-300`}
                                  style={{ width: `${barWidth}%` }}
                                />
                              </div>
                              <span className={`text-xs font-bold ${currentDraftAction.action === 'ban' ? 'text-red-400' : 'text-green-400'} min-w-[35px] text-right`}>
                                {currentDraftAction.action === 'ban' ? '' : '+'}{valuePercent.toFixed(1)}%
                              </span>
                            </div>

                            {/* Top Reason */}
                            {rec.reasons && rec.reasons[0] && (
                              <div className="text-xs text-gray-400 mt-1 truncate">
                                {rec.reasons[0]}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
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


        {/* Post-Draft Analysis */}
        {showAnalysis && analysis && (
          <div className="mt-8">
            <AnalysisPanel 
              analysis={analysis}
              onClose={() => setShowAnalysis(false)}
            />
          </div>
        )}

        {/* Analysis Loading State */}
        {analyzing && (
          <div className="mt-8 bg-gray-800 border border-gray-700 rounded-lg p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin text-gold-500 mx-auto mb-4" />
            <p className="text-gray-400">Analyzing draft composition...</p>
          </div>
        )}
      </div>
    </div>
  );
}
