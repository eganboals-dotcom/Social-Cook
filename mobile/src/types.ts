/** Shared data types mirroring the backend contracts. */

export interface Ingredient {
  name: string;
  amount?: string | null;
  unit?: string | null;
}

export interface Step {
  order: number;
  text: string;
}

export interface ExtractedRecipe {
  title: string;
  servings?: string | null;
  ingredients: Ingredient[];
  steps: Step[];
}

export interface ExtractResponse {
  recipe: ExtractedRecipe;
  source_platform?: string | null;
  raw_extraction: Record<string, unknown>;
}

/** Payload for POST /recipes and /recipes/import. */
export interface RecipeCreate extends ExtractedRecipe {
  source_url?: string | null;
  source_platform?: string | null;
  raw_extraction?: Record<string, unknown> | null;
}

export interface SavedRecipe {
  id: number;
  source_url?: string | null;
  source_platform?: string | null;
  title: string;
  servings?: string | null;
  ingredients: Ingredient[];
  steps: Step[];
  created_at: string;
}

export interface RecipeSaveResponse {
  recipe: SavedRecipe;
  already_saved: boolean;
}

export interface RecipeListResponse {
  recipes: SavedRecipe[];
  saved_recipe_count: number;
  saved_recipe_cap: number;
}

export interface RecipeImportResult {
  imported: number;
  duplicates: number;
  skipped_over_cap: number;
  saved_recipe_count: number;
  saved_recipe_cap: number;
}

export interface User {
  id: number;
  email: string;
  saved_recipe_cap: number;
  saved_recipe_count: number;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UnlockConfig {
  free_cap: number;
  cap_increment: number;
  unlock_price_usd: number;
  product_id: string;
}

export interface ValidateResponse {
  credited: number;
  saved_recipe_cap: number;
  saved_recipe_count: number;
}
