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
  win_probability: number;
  confidence: number;
  explanations: Explanation[];
  model_version: string;
  timestamp: string;
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
  champ_index: Record<string, number>; // name -> index
  id_to_index: Record<string, number>; // championId -> index
  tags: Record<string, Champion['tags']>; // championId -> tags
}

export interface APIError {
  detail: string;
  status?: number;
}

