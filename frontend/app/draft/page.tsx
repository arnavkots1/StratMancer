'use client';

import { useState, useEffect, useMemo, useCallback, type ReactNode } from 'react';
import { AlertCircle, Loader2, Sparkles, Shield, TrendingUp } from 'lucide-react';
import { LayoutGroup, m } from 'framer-motion';
import dynamic from 'next/dynamic';
import EloSelector, { type EloGroup } from '@/components/EloSelector';

// Lazy load heavy components
const ChampionPicker = dynamic(() => import('@/components/ChampionPicker'), {
  loading: () => <div className="flex items-center justify-center p-8"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>,
  ssr: false
});

const PredictionCard = dynamic(() => import('@/components/PredictionCard'), {
  loading: () => <div className="flex items-center justify-center p-4"><div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>,
  ssr: false
});

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Container } from '@/components/Section';
import { api } from '@/lib/api';
import { fadeUp, scaleIn } from '@/lib/motion';
import { DraftBoard, type DraftAction } from '@/components/draft/DraftBoard';
import { RecommendationsPanel } from '@/components/draft/RecommendationsPanel';
import { ConfidenceIndicator } from '@/components/ConfidenceIndicator';
import { DataWarning } from '@/components/DataWarning';
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
  const [recommendations, setRecommendations] = useState<any>(null);
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [recommendationError, setRecommendationError] = useState<string | null>(null);

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

  const totalSteps = DRAFT_SEQUENCE.length;

  const lockedChampionIds = useMemo(() => {
    const picked = [
      ...Object.values(draftState.blue),
      ...Object.values(draftState.red),
    ]
      .filter((champ): champ is Champion => Boolean(champ))
      .map((champ) => parseInt(champ.id, 10));

    const banned = [...draftState.blueBans, ...draftState.redBans]
      .filter((champ): champ is Champion => Boolean(champ))
      .map((champ) => parseInt(champ.id, 10));

    return new Set<number>([...picked, ...banned]);
  }, [draftState.blue, draftState.red, draftState.blueBans, draftState.redBans]);

  const lockedChampionNames = useMemo(() => {
    const names = [
      ...Object.values(draftState.blue),
      ...Object.values(draftState.red),
      ...draftState.blueBans,
      ...draftState.redBans,
    ]
      .filter((champ): champ is Champion => Boolean(champ))
      .map((champ) => champ.name);

    return new Set<string>(names);
  }, [draftState.blue, draftState.red, draftState.blueBans, draftState.redBans]);

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
      const featureMap = await api.getFeatureMap() as FeatureMap;
      
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
      setPrediction(result as PredictionResponse);
      
    } catch (err: any) {
      console.error('Prediction failed:', err);
      setError(err.message || 'Prediction failed. Please try again.');
    } finally {
      setPredicting(false);
    }
  };


  const handleGetRecommendations = useCallback(async () => {
    if (!currentDraftAction) return;

    setRecommendationLoading(true);
    setRecommendationError(null);

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
  }, [currentDraftAction, draftState]);

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
      setRecommendations(null);
    } else {
      console.error('Champion not found for ID:', championId);
    }
  };

  const handleRemovePickSlot = useCallback((team: 'blue' | 'red', role: keyof TeamComposition) => {
    setDraftState(prev => ({
      ...prev,
      [team]: {
        ...prev[team],
        [role]: null,
      },
    }));
  }, []);

  const handleRemoveBanSlot = useCallback((team: 'blue' | 'red', index: number) => {
    setDraftState(prev => {
      const updatedBans = team === 'blue' ? [...prev.blueBans] : [...prev.redBans];
      updatedBans.splice(index, 1);
      return {
        ...prev,
        blueBans: team === 'blue' ? updatedBans : prev.blueBans,
        redBans: team === 'red' ? updatedBans : prev.redBans,
      };
    });
  }, []);

  const handleStartDraft = useCallback(() => {
    setDraftStarted(true);
    setTimerActive(true);
    setPickTimer(30);
  }, []);

  const handleToggleTimer = useCallback(() => {
    setTimerActive(prev => {
      const next = !prev;
      if (next) {
        setPickTimer(30);
      }
      return next;
    });
  }, []);

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
    setRecommendations(null);
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
      <div className="min-h-screen flex items-center justify-center bg-[#060911]">
        <m.div
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col items-center gap-4 rounded-3xl border border-white/10 bg-[#0c1424]/80 px-12 py-10 text-white/70 shadow-[0_45px_120px_-60px_rgba(6,9,17,0.9)] backdrop-blur-xl"
        >
          <div className="relative">
            <Loader2 className="h-16 w-16 animate-spin text-accent" />
            <div className="absolute inset-0 h-16 w-16 rounded-full bg-accent/20 blur-2xl" />
          </div>
          <p className="text-lg font-semibold text-white">Initializing Draft Matrix…</p>
          <p className="text-sm text-white/60">Downloading champion telemetry and model context</p>
        </m.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#060911]">
      <Container size="xl" className="py-16 lg:py-20">
        <LayoutGroup>
          <m.div
            initial="initial"
            animate="animate"
            variants={fadeUp}
            className="space-y-12"
          >
            <m.header
              variants={scaleIn}
              className="relative overflow-hidden rounded-[32px] border border-white/10 bg-gradient-to-br from-primary/12 via-[#0d1424]/85 to-secondary/10 p-10 backdrop-blur-xl shadow-[0_45px_140px_-80px_rgba(7,10,17,0.9)]"
            >
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_right,rgba(6,182,212,0.25),transparent_55%)] opacity-60" />
              <div className="relative flex flex-col gap-8 lg:flex-row lg:items-start lg:justify-between">
                <div className="max-w-3xl space-y-4">
                  <Badge className="w-fit border-white/20 bg-white/10 px-4 py-2 text-xs uppercase tracking-[0.32em] text-white/60">
                    Live Draft Intelligence
                  </Badge>
                  <h1 className="text-3xl font-semibold text-white md:text-5xl">
                    Holographic Draft Command Window
                  </h1>
                  <p className="max-w-xl text-sm text-white/65 md:text-base">
                    Coordinate bans and picks with StratMancer&apos;s predictive engine. Watch AI reasoning unfold
                    as we forecast every matchup pivot in real-time.
                  </p>
                </div>
                <div className="grid w-full gap-4 sm:grid-cols-3 lg:w-auto">
                  <MetricPill icon={<Sparkles className="h-4 w-4 text-accent" />} label="Model" value={draftState.elo.toUpperCase()} />
                  <MetricPill icon={<Shield className="h-4 w-4 text-sky-300" />} label="Phase" value={currentDraftAction ? (currentDraftAction.action === 'ban' ? 'Ban Round' : `${currentDraftAction.role?.toUpperCase()} Pick`) : 'Complete'} />
                  <MetricPill icon={<TrendingUp className="h-4 w-4 text-emerald-300" />} label="Steps" value={`${Math.min(draftStep + 1, totalSteps)}/${totalSteps}`} />
                </div>
              </div>
            </m.header>

            {/* Data Warning */}
            <DataWarning variant="warning" />

            {/* Confidence Indicator */}
            <m.div
              variants={fadeUp}
              className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur"
            >
              <div className="flex items-center gap-4">
                <div className="text-sm text-white/80">Draft Confidence:</div>
                <ConfidenceIndicator
                  confidence={prediction?.confidence || 0}
                  filledSlots={Object.values(draftState.blue).filter(Boolean).length + Object.values(draftState.red).filter(Boolean).length}
                  totalSlots={10}
                />
              </div>
              <div className="text-xs text-white/60">
                {prediction ? 'AI Analysis Active' : 'Awaiting Draft Data'}
              </div>
            </m.div>

            {error && (
              <m.div
                variants={scaleIn}
                className="relative overflow-hidden rounded-2xl border border-red-500/40 bg-red-500/10 px-5 py-4 text-sm text-red-200 backdrop-blur"
              >
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 flex-shrink-0" />
                  <p className="flex-1">{error}</p>
                  <button
                    onClick={() => setError(null)}
                    className="text-lg leading-none text-red-300 transition hover:text-red-100"
                  >
                    ×
                  </button>
                </div>
              </m.div>
            )}

            <DraftBoard
              draftState={draftState}
              currentAction={currentDraftAction as DraftAction | null}
              draftStep={draftStep}
              totalSteps={totalSteps}
              draftStarted={draftStarted}
              pickTimer={pickTimer}
              timerActive={timerActive}
              onToggleTimer={handleToggleTimer}
              onStartDraft={handleStartDraft}
              onResetDraft={handleResetDraft}
              onRemovePick={handleRemovePickSlot}
              onRemoveBan={handleRemoveBanSlot}
            />

            <m.section
              variants={fadeUp}
              className="grid gap-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]"
            >
              <RecommendationsPanel
                currentAction={currentDraftAction as DraftAction | null}
                recommendations={recommendations?.recommendations ?? null}
                loading={recommendationLoading}
                error={recommendationError}
                lockedChampionIds={lockedChampionIds}
                lockedChampionNames={lockedChampionNames}
                onSelectRecommendation={handleSelectRecommendation}
                champions={champions}
              />

              <div className="flex flex-col gap-6">
                <m.div
                  variants={scaleIn}
                  className="relative overflow-hidden rounded-[28px] border border-white/10 bg-[#0d1424]/80 p-6 backdrop-blur-xl"
                >
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(124,58,237,0.25),transparent_60%)] opacity-50" />
                  <div className="relative space-y-6">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="w-full max-w-sm space-y-2">
                        <p className="text-xs uppercase tracking-[0.28em] text-white/40">Rank Model</p>
                        <EloSelector
                          value={draftState.elo as EloGroup}
                          onChange={async (elo) => {
                            setDraftState(prev => ({ ...prev, elo: elo as Elo }));
                            setPrediction(null);
                            setRecommendations(null);
                            setError(null);
                            setRecommendationError(null);
                            try {
                              await api.refreshContext(elo);
                            } catch (err) {
                              console.warn('Failed to refresh backend context:', err);
                            }
                          }}
                        />
                      </div>
                      <div className="w-full max-w-sm space-y-2">
                        <p className="text-xs uppercase tracking-[0.28em] text-white/40">Patch Override</p>
                        <input
                          type="text"
                          value={draftState.patch || ''}
                          onChange={(e) => setDraftState(prev => ({ ...prev, patch: e.target.value }))}
                          placeholder="15.20"
                          className="w-full rounded-xl border border-white/20 bg-black/40 px-4 py-3 text-sm text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-primary/40"
                        />
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-4">
                      <Button
                        onClick={handlePredictDraft}
                        disabled={predicting}
                        className="flex items-center gap-2 rounded-xl border border-primary/40 bg-gradient-to-r from-primary/80 via-primary to-secondary px-6 py-3 text-xs uppercase tracking-[0.28em] text-primary-foreground shadow-[0_0_40px_rgba(124,58,237,0.35)]"
                      >
                        {predicting ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Calculating
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-4 w-4" />
                            Analyze Draft
                          </>
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={handleResetDraft}
                        className="rounded-xl border border-white/10 bg-black/30 px-6 py-3 text-xs uppercase tracking-[0.28em] text-white/60 hover:text-white"
                      >
                        Reset Board
                      </Button>
                    </div>
                  </div>
                </m.div>

                <m.div
                  variants={scaleIn}
                  className="rounded-[28px] border border-white/10 bg-[#0d1424]/60 p-6 backdrop-blur"
                >
                  <div className="grid gap-4 sm:grid-cols-3">
                    <SummaryStat label="Draft Started" value={draftStarted ? 'Yes' : 'No'} />
                    <SummaryStat label="Pending Actions" value={currentDraftAction ? `${totalSteps - draftStep - 1}` : '0'} />
                    <SummaryStat label="Insight Ready" value="—" />
                  </div>
                </m.div>
              </div>
            </m.section>

            {prediction && (
              <m.section
                variants={fadeUp}
                className="rounded-[32px] border border-white/10 bg-[#0d1424]/80 p-8 backdrop-blur-xl"
              >
                <PredictionCard prediction={prediction} />
              </m.section>
            )}

            <m.section
              variants={fadeUp}
              className="rounded-[32px] border border-white/10 bg-[#0d1424]/80 p-6 backdrop-blur-xl"
            >
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
            </m.section>


          </m.div>
        </LayoutGroup>
      </Container>
    </div>
  );
}

type MetricPillProps = {
  icon: ReactNode
  label: string
  value: string
}

function MetricPill({ icon, label, value }: MetricPillProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-white/70 backdrop-blur">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.28em] text-white/40">
        {icon}
        <span>{label}</span>
      </div>
      <div className="mt-2 text-lg font-semibold text-white">{value}</div>
    </div>
  )
}

type SummaryStatProps = {
  label: string
  value: string
}

function SummaryStat({ label, value }: SummaryStatProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/25 px-4 py-3 backdrop-blur">
      <p className="text-[11px] uppercase tracking-[0.28em] text-white/35">{label}</p>
      <p className="mt-2 text-base font-semibold text-white/80">{value}</p>
    </div>
  )
}
