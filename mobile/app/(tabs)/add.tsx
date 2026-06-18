import { useState } from 'react';
import { Alert, StyleSheet, Text } from 'react-native';
import { useRouter } from 'expo-router';

import * as api from '../../src/api/client';
import { ApiError } from '../../src/api/client';
import { useAuth } from '../../src/auth/AuthContext';
import { Banner } from '../../src/components/Banner';
import { Button } from '../../src/components/Button';
import { RecipeView } from '../../src/components/RecipeView';
import { Screen } from '../../src/components/Screen';
import { TextField } from '../../src/components/TextField';
import { addLocalRecipe } from '../../src/storage/localRecipes';
import { colors } from '../../src/theme';
import type { ExtractedRecipe, RecipeCreate } from '../../src/types';

interface Extracted {
  recipe: ExtractedRecipe;
  platform: string | null;
  raw: Record<string, unknown>;
  sourceUrl: string;
}

export default function AddScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const [url, setUrl] = useState('');
  const [caption, setCaption] = useState('');
  const [showCaption, setShowCaption] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extracted, setExtracted] = useState<Extracted | null>(null);

  async function onExtract() {
    setError(null);
    setExtracted(null);
    const link = url.trim();
    if (!link) {
      setError('Paste a link to a cooking video first.');
      return;
    }
    setLoading(true);
    try {
      const resp = await api.extractRecipe(link, caption.trim() || undefined);
      setExtracted({
        recipe: resp.recipe,
        platform: resp.source_platform ?? null,
        raw: resp.raw_extraction,
        sourceUrl: link,
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong extracting that recipe.');
    } finally {
      setLoading(false);
    }
  }

  async function onSave() {
    if (!extracted) return;
    setSaving(true);
    setError(null);
    const payload: RecipeCreate = {
      ...extracted.recipe,
      source_url: extracted.sourceUrl,
      source_platform: extracted.platform,
      raw_extraction: extracted.raw,
    };
    try {
      if (user) {
        const saved = await api.saveRecipe(payload);
        reset();
        router.push(`/recipe/${saved.recipe.id}`);
      } else {
        await addLocalRecipe(payload);
        reset();
        router.push('/(tabs)/recipes');
      }
    } catch (e) {
      if (e instanceof ApiError && e.status === 402) {
        Alert.alert('Recipe limit reached', e.message, [{ text: 'OK' }]);
      } else {
        setError(e instanceof ApiError ? e.message : 'Could not save this recipe.');
      }
    } finally {
      setSaving(false);
    }
  }

  function reset() {
    setExtracted(null);
    setUrl('');
    setCaption('');
    setShowCaption(false);
  }

  return (
    <Screen scroll>
      <Text style={styles.intro}>
        Paste a link to a TikTok, Reel, or YouTube Short. Adding the caption text gives the best
        results.
      </Text>

      <TextField
        label="Video link"
        placeholder="https://..."
        value={url}
        onChangeText={setUrl}
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="url"
      />

      <Button
        title={showCaption ? 'Hide caption field' : 'Add caption text (recommended)'}
        variant="ghost"
        onPress={() => setShowCaption((s) => !s)}
      />
      {showCaption ? (
        <TextField
          label="Caption / description"
          placeholder="Paste the post caption here"
          value={caption}
          onChangeText={setCaption}
          multiline
        />
      ) : null}

      <Button title="Extract recipe" onPress={onExtract} loading={loading} />

      {error ? <Banner tone="danger">{error}</Banner> : null}

      {extracted ? (
        <>
          <RecipeView
            title={extracted.recipe.title}
            servings={extracted.recipe.servings}
            ingredients={extracted.recipe.ingredients}
            steps={extracted.recipe.steps}
          />
          <Button
            title={user ? 'Save to my recipes' : 'Save on this device'}
            onPress={onSave}
            loading={saving}
          />
          {!user ? (
            <Banner tone="info">
              Saved on this device. Create an account to sync everywhere — your local recipes come
              with you.
            </Banner>
          ) : null}
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  intro: { fontSize: 15, color: colors.subtle, lineHeight: 21 },
});
