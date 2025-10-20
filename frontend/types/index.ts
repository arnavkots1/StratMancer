/**
 * Type definitions for StratMancer frontend
 */

export type Role = 'TOP' | 'JUNGLE' | 'MID' | 'ADC' | 'SUPPORT';
export type Team = 'blue' | 'red';
export type Elo = 'low' | 'mid' | 'high';

export interface Champion {
  id: string;
  name: string;
  key: string; // Numeric key as string
  roles: Role[];
  tags: {
    damage?: string[];
    role?: string[];
    mobility?: string;
    engage?: number;
    hard_cc?: number;
    sustain?: number;
    [key: string]: any;
  };
}

export interface TeamComposition {
  top: Champion | null;
  jungle: Champion | null;
  mid: Champion | null;
  adc: Champion | null;
  support: Champion | null;
}

export interface DraftState {
  blue: TeamComposition;
  red: TeamComposition;
  blueBans: Champion[];
  redBans: Champion[];
  elo: Elo;
  patch?: string;
}

export interface PredictionRequest {
  blue_team: number[]; // Champion IDs
  red_team: number[];
  blue_bans?: number[];
  red_bans?: number[];
  elo?: Elo;
  patch?: string;
}

export interface PredictionResponse {
  blue_win_prob: number;
  red_win_prob: number;
  confidence: number;
  calibrated: boolean;
  explanations: string[];
  model_version: string;
  elo_group: string;
  patch: string;
}

export interface Explanation {
  factor: string;
  impact: number; // Positive = helps blue, negative = hurts blue
  description: string;
}

export interface FeatureMap {
  meta: {
    version: string;
    patch: string;
    num_champ: number;
    created_at: string;
  };
  champ_index: Record<string, number>; // name -> championId
  id_to_index: Record<string, number>; // championId -> index
  tags: Record<string, Champion['tags']>; // championId -> tags
}

export interface APIError {
  detail: string;
  status?: number;
}

export interface MetaChampion {
  champion_id: number;
  champion_name: string;
  pick_rate: number;
  win_rate: number;
  ban_rate: number;
  delta_win_rate: number;
  performance_index: number;
  games_played: number;
  wins: number;
  bans: number;
}

export interface MetaSnapshot {
  elo: Elo | string;
  patch: string;
  last_updated: string;
  previous_patch?: string | null;
  total_matches: number;
  champion_count: number;
  available_patches: string[];
  champions: MetaChampion[];
}

export interface MetaTrendEntry {
  champion_id: number;
  champion_name: string;
  delta_win_rate: number;
  current_win_rate: number;
  previous_win_rate?: number | null;
  performance_index: number;
}

export interface MetaTrends {
  elo: Elo | string;
  latest_patch?: string | null;
  previous_patch?: string | null;
  generated_at: string;
  risers: MetaTrendEntry[];
  fallers: MetaTrendEntry[];
}
