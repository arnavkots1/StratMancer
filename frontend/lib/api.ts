/**
 * API Client for StratMancer Backend
 * 
 * Provides typed fetch wrappers with error handling, timeouts, and abort signals.
 * All endpoints match the FastAPI backend routes exactly.
 */

import type { RequestInit as NextRequestInit } from 'next/dist/server/web/spec-extension/request'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

type RequestOptions = Omit<NextRequestInit, 'signal'> & {
  signal?: AbortSignal;
  timeoutMs?: number;
  revalidate?: number | false;
};

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function withTimeout(signal?: AbortSignal, timeoutMs = 30_000) {
  if (signal) return signal;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const { signal: controllerSignal } = controller;
  controllerSignal.addEventListener('abort', () => clearTimeout(timer));
  return controllerSignal;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { timeoutMs, ...rest } = options;
  const signal = await withTimeout(rest.signal, timeoutMs);
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...rest,
    signal,
    headers: {
      'Content-Type': 'application/json',
      'X-STRATMANCER-KEY': process.env.NEXT_PUBLIC_API_KEY || 'dev-key-change-in-production',
      ...(rest.headers ?? {}),
    },
    next: options.revalidate === false ? { revalidate: 0 } : { revalidate: options.revalidate ?? 30 },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new ApiError(message || 'API request failed', response.status);
  }

  if (response.status === 204) {
    return null as T;
  }

  return (await response.json()) as T;
}

export const api = {
  // Draft Prediction
  predictDraft(payload: Record<string, unknown>, options?: RequestOptions) {
    return request('/predict-draft', { method: 'POST', body: JSON.stringify(payload), ...options });
  },

  // Refresh Context (force rebuild of feature context)
  refreshContext(elo?: string, options?: RequestOptions) {
    return request('/predict-draft/refresh-context', { 
      method: 'POST', 
      body: JSON.stringify({ elo }), 
      ...options 
    });
  },

  // Pick Recommendations
  getPickRecommendations(payload: Record<string, unknown>, options?: RequestOptions) {
    return request('/recommend/pick', { method: 'POST', body: JSON.stringify(payload), ...options });
  },

  // Ban Recommendations
  getBanRecommendations(payload: Record<string, unknown>, options?: RequestOptions) {
    return request('/recommend/ban', { method: 'POST', body: JSON.stringify(payload), ...options });
  },

  // Draft Analysis
  analyzeDraft(payload: Record<string, unknown>, options?: RequestOptions) {
    return request('/analysis/draft', { method: 'POST', body: JSON.stringify(payload), ...options });
  },

  // Feature Map (champion data with IDs, tags, etc.)
  getFeatureMap(options?: RequestOptions) {
    return request('/models/feature-map', { method: 'GET', ...options });
  },

  // Meta Endpoints
  getMetaOverview(elo: string, options?: RequestOptions) {
    return request(`/meta/${elo}/latest`, { method: 'GET', ...options });
  },

  getMetaTrends(elo: string, options?: RequestOptions) {
    return request(`/meta/trends/${elo}`, { method: 'GET', ...options });
  },

  getMetaForPatch(elo: string, patch: string, options?: RequestOptions) {
    return request(`/meta/${elo}/${patch}`, { method: 'GET', ...options });
  },

  // Model Registry
  getModels(options?: RequestOptions) {
    return request('/models/registry', { method: 'GET', ...options });
  },

  // Landing Page Data
  getLandingData(options?: RequestOptions) {
    return request('/landing/', { method: 'GET', ...options });
  },

  // Health Check
  health(options?: RequestOptions) {
    return request('/health', { method: 'GET', ...options });
  },
};
