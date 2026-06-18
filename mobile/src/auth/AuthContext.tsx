/**
 * Auth state + session persistence.
 *
 * The JWT is stored in expo-secure-store and re-applied to the API client on
 * launch. On sign-up/login any locally-saved recipes are migrated into the
 * account (local-first), then the user is refreshed to reflect the new count.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import * as SecureStore from 'expo-secure-store';

import * as api from '../api/client';
import { setAuthToken } from '../api/client';
import {
  clearPurchasesUser,
  configurePurchases,
  setPurchasesUser,
} from '../purchases/purchases';
import { clearLocalRecipes, getLocalRecipes, toRecipeCreate } from '../storage/localRecipes';
import type { TokenResponse, User } from '../types';

const TOKEN_KEY = 'social_cook_token';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  forgotPassword: (email: string) => Promise<string>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        configurePurchases();
        const token = await SecureStore.getItemAsync(TOKEN_KEY);
        if (token) {
          setAuthToken(token);
          try {
            const restored = await api.me();
            setUser(restored);
            await setPurchasesUser(String(restored.id));
          } catch {
            await SecureStore.deleteItemAsync(TOKEN_KEY);
            setAuthToken(null);
          }
        }
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const migrateLocalRecipes = useCallback(async () => {
    const local = await getLocalRecipes();
    if (local.length === 0) return;
    try {
      await api.importRecipes(local.map(toRecipeCreate));
      await clearLocalRecipes();
    } catch {
      // Keep local recipes if migration fails; user can retry later.
    }
  }, []);

  const completeAuth = useCallback(
    async (resp: TokenResponse) => {
      await SecureStore.setItemAsync(TOKEN_KEY, resp.access_token);
      setAuthToken(resp.access_token);
      setUser(resp.user);
      await setPurchasesUser(String(resp.user.id));
      await migrateLocalRecipes();
      try {
        setUser(await api.me());
      } catch {
        // non-fatal
      }
    },
    [migrateLocalRecipes],
  );

  const signIn = useCallback(
    async (email: string, password: string) => completeAuth(await api.login(email, password)),
    [completeAuth],
  );

  const signUp = useCallback(
    async (email: string, password: string) => completeAuth(await api.signup(email, password)),
    [completeAuth],
  );

  const signOut = useCallback(async () => {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    setAuthToken(null);
    setUser(null);
    await clearPurchasesUser();
  }, []);

  const forgotPassword = useCallback(async (email: string) => {
    const { message } = await api.forgotPassword(email);
    return message;
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      setUser(await api.me());
    } catch {
      // ignore
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, signIn, signUp, signOut, forgotPassword, refreshUser }),
    [user, loading, signIn, signUp, signOut, forgotPassword, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
