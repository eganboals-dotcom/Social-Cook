import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';

import * as api from '../../src/api/client';
import { ApiError } from '../../src/api/client';
import { useAuth } from '../../src/auth/AuthContext';
import { Banner } from '../../src/components/Banner';
import { Button } from '../../src/components/Button';
import { RecipeCard } from '../../src/components/RecipeCard';
import { Screen } from '../../src/components/Screen';
import { TextField } from '../../src/components/TextField';
import { getLocalRecipes } from '../../src/storage/localRecipes';
import { colors, spacing } from '../../src/theme';
import type { Ingredient, Step } from '../../src/types';

interface Row {
  key: string;
  title: string;
  subtitle: string;
  onPress: () => void;
}

function metaLine(rec: {
  ingredients: Ingredient[];
  steps: Step[];
  source_platform?: string | null;
}): string {
  const parts = [`${rec.ingredients.length} ingredients`, `${rec.steps.length} steps`];
  if (rec.source_platform) parts.push(rec.source_platform);
  return parts.join('  ·  ');
}

export default function RecipesScreen() {
  const { user } = useAuth();
  const router = useRouter();
  const [q, setQ] = useState('');
  const [rows, setRows] = useState<Row[]>([]);
  const [cap, setCap] = useState<{ count: number; cap: number } | null>(null);
  const [localCount, setLocalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      if (user) {
        const r = await api.listRecipes(q.trim() || undefined);
        setCap({ count: r.saved_recipe_count, cap: r.saved_recipe_cap });
        setRows(
          r.recipes.map((rec) => ({
            key: `r${rec.id}`,
            title: rec.title,
            subtitle: metaLine(rec),
            onPress: () => router.push(`/recipe/${rec.id}`),
          })),
        );
      } else {
        let local = await getLocalRecipes();
        setLocalCount(local.length);
        const needle = q.trim().toLowerCase();
        if (needle) local = local.filter((x) => x.title.toLowerCase().includes(needle));
        setCap(null);
        setRows(
          local.map((rec) => ({
            key: rec.localId,
            title: rec.title,
            subtitle: metaLine(rec),
            onPress: () =>
              router.push({ pathname: '/recipe/[id]', params: { id: rec.localId, local: '1' } }),
          })),
        );
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load your recipes.');
    }
  }, [user, q, router]);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      load().finally(() => setLoading(false));
    }, [load]),
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  return (
    <Screen>
      <TextField
        placeholder="Search your recipes"
        value={q}
        onChangeText={setQ}
        autoCapitalize="none"
        autoCorrect={false}
      />

      {user && cap ? (
        <Text style={styles.count}>
          {cap.count} of {cap.cap} saved
        </Text>
      ) : null}

      {!user ? (
        <>
          <Banner tone="info">
            {localCount > 0 ? `${localCount} saved on this device. ` : ''}Sign in to sync your
            recipes and save more.
          </Banner>
          <Button
            title="Sign in / Create account"
            variant="secondary"
            onPress={() => router.push('/login')}
          />
        </>
      ) : null}

      {error ? <Banner tone="danger">{error}</Banner> : null}

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.accent} />
        </View>
      ) : (
        <FlatList
          style={styles.list}
          data={rows}
          keyExtractor={(item) => item.key}
          renderItem={({ item }) => (
            <RecipeCard title={item.title} subtitle={item.subtitle} onPress={item.onPress} />
          )}
          ItemSeparatorComponent={() => <View style={styles.sep} />}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} />
          }
          ListEmptyComponent={
            error ? null : (
              <Text style={styles.empty}>No recipes yet. Add one from the Add tab.</Text>
            )
          }
        />
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  count: { fontSize: 13, color: colors.subtle, fontWeight: '600' },
  list: { flex: 1 },
  listContent: { paddingVertical: spacing(2) },
  sep: { height: spacing(2.5) },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  empty: { textAlign: 'center', color: colors.muted, marginTop: spacing(8) },
});
