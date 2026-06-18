/**
 * Thin, typed client for the Social Cook backend.
 *
 * The access token is held here and injected as a Bearer header — the auth
 * context calls `setAuthToken` on login/restore/logout so screens don't have to
 * thread it through. Everything goes through `request()` for consistent errors.
 */
import { API_BASE_URL } from '../config';
import type {
  ExtractResponse,
  RecipeCreate,
  RecipeImportResult,
  RecipeListResponse,
  RecipeSaveResponse,
  SavedRecipe,
  TokenResponse,
  User,
} from '../types';

let authToken: string | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token;
}

export class ApiError extends Error {
  status?: number;
  payload?: unknown;
  constructor(message: string, status?: number, payload?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

function messageFromDetail(detail: unknown, status: number): string {
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object') {
    // Cap error: { message, saved_recipe_count, saved_recipe_cap }
    const maybe = detail as { message?: unknown };
    if (typeof maybe.message === 'string') return maybe.message;
    // pydantic 422: [{ msg, loc }...]
    if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
  }
  return `Request failed (${status})`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw new ApiError(`Couldn't reach the server at ${API_BASE_URL}. Is it running?`);
  }

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new ApiError(messageFromDetail(data?.detail, res.status), res.status, data?.detail);
  }
  return data as T;
}

// --- Health ---
export function checkHealth(): Promise<{ status: string }> {
  return request('/health');
}

// --- Auth ---
export function signup(email: string, password: string): Promise<TokenResponse> {
  return request('/auth/signup', { method: 'POST', body: JSON.stringify({ email, password }) });
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
}

export function me(): Promise<User> {
  return request('/auth/me');
}

export function forgotPassword(email: string): Promise<{ message: string }> {
  return request('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) });
}

// --- Extraction ---
export function extractRecipe(url: string, caption?: string): Promise<ExtractResponse> {
  return request('/extract', { method: 'POST', body: JSON.stringify({ url, caption }) });
}

// --- Recipes ---
export function saveRecipe(payload: RecipeCreate): Promise<RecipeSaveResponse> {
  return request('/recipes', { method: 'POST', body: JSON.stringify(payload) });
}

export function listRecipes(q?: string): Promise<RecipeListResponse> {
  const qs = q ? `?q=${encodeURIComponent(q)}` : '';
  return request(`/recipes${qs}`);
}

export function getRecipe(id: number): Promise<SavedRecipe> {
  return request(`/recipes/${id}`);
}

export function updateRecipe(id: number, patch: Partial<RecipeCreate>): Promise<SavedRecipe> {
  return request(`/recipes/${id}`, { method: 'PATCH', body: JSON.stringify(patch) });
}

export async function deleteRecipe(id: number): Promise<void> {
  await request(`/recipes/${id}`, { method: 'DELETE' });
}

export function importRecipes(items: RecipeCreate[]): Promise<RecipeImportResult> {
  return request('/recipes/import', { method: 'POST', body: JSON.stringify(items) });
}
