/**
 * Local-first recipe storage (AsyncStorage).
 *
 * Lets a user save recipes before creating an account. On sign-up/login the
 * auth context migrates these into the account via POST /recipes/import and
 * clears them.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

import type { RecipeCreate } from '../types';

const KEY = 'social_cook_local_recipes_v1';

export interface LocalRecipe extends RecipeCreate {
  localId: string;
  created_at: string;
}

export async function getLocalRecipes(): Promise<LocalRecipe[]> {
  const raw = await AsyncStorage.getItem(KEY);
  return raw ? (JSON.parse(raw) as LocalRecipe[]) : [];
}

async function saveAll(list: LocalRecipe[]): Promise<void> {
  await AsyncStorage.setItem(KEY, JSON.stringify(list));
}

export async function addLocalRecipe(recipe: RecipeCreate): Promise<LocalRecipe> {
  const list = await getLocalRecipes();
  // Soft duplicate handling mirrors the backend (same source_url -> existing).
  if (recipe.source_url) {
    const existing = list.find((r) => r.source_url === recipe.source_url);
    if (existing) return existing;
  }
  const item: LocalRecipe = {
    ...recipe,
    localId: `${Date.now()}-${Math.round(Math.random() * 1e6)}`,
    created_at: new Date().toISOString(),
  };
  await saveAll([item, ...list]);
  return item;
}

export async function getLocalRecipe(localId: string): Promise<LocalRecipe | undefined> {
  return (await getLocalRecipes()).find((r) => r.localId === localId);
}

export async function updateLocalRecipe(
  localId: string,
  patch: Partial<RecipeCreate>,
): Promise<LocalRecipe | undefined> {
  const list = await getLocalRecipes();
  let updated: LocalRecipe | undefined;
  const next = list.map((r) => {
    if (r.localId !== localId) return r;
    updated = { ...r, ...patch };
    return updated;
  });
  await saveAll(next);
  return updated;
}

export async function deleteLocalRecipe(localId: string): Promise<void> {
  const list = await getLocalRecipes();
  await saveAll(list.filter((r) => r.localId !== localId));
}

export async function clearLocalRecipes(): Promise<void> {
  await AsyncStorage.removeItem(KEY);
}

export function toRecipeCreate(local: LocalRecipe): RecipeCreate {
  const { localId: _localId, created_at: _createdAt, ...rest } = local;
  return rest;
}
