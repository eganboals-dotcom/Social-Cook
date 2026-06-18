/**
 * Thin, typed client for the Social Cook backend.
 *
 * Feature endpoints (auth, extraction, recipes, purchases) are layered on in
 * later phases. Everything goes through `request()` so error handling and
 * headers stay consistent.
 */
import { API_BASE_URL } from '../config';

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError(`Could not reach the backend at ${API_BASE_URL}. Is it running?`);
  }
  if (!res.ok) {
    throw new ApiError(`Request failed (${res.status})`, res.status);
  }
  return (await res.json()) as T;
}

export interface HealthResponse {
  status: string;
}

export function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}
