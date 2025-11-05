/**
 * Draft IQ v2 API client
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'dev-key-change-in-production';

export interface DraftIQV2Payload {
  elo: 'low' | 'mid' | 'high';
  patch: string;
  blue: {
    top: number;
    jgl: number;
    mid: number;
    adc: number;
    sup: number;
    bans: number[];
  };
  red: {
    top: number;
    jgl: number;
    mid: number;
    adc: number;
    sup: number;
    bans: number[];
  };
}

export interface DraftIQV2Response {
  json: any;
  markdown: string;
}

export async function explainDraftV2(
  payload: DraftIQV2Payload
): Promise<DraftIQV2Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 40000); // 40s timeout (backend uses 30s + buffer)

  try {
    const res = await fetch(`${API_BASE}/draft-iq/v2/explain`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-STRATMANCER-KEY': API_KEY,
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(`Draft IQ v2 failed: ${error.detail || res.statusText}`);
    }

    return res.json();
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Draft IQ v2 request timeout');
    }
    throw error;
  }
}

