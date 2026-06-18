import { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';

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
  // Set when the app is opened via the share sheet (see app/_layout.tsx).
  const params = useLocalSearchParams<{ sharedUrl?: string; sharedText?: string }>();

  const [url, setUrl] = useState('');
  const [caption, setCaption] = useState('');
  const [showCaption, setShowCaption] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extracted, setExtracted] = useState<Extracted | null>(null);

  const handledShareRef = useRef('');

  async function runExtract(link: string, cap?: string) {
    setError(null);
    setExtracted(null);
    if (!link) {
      setError('Paste a link to a cooking video first.');
      return;
    }
    setLoading(true);
    try {
      const resp = await api.extractRecipe(link, cap);
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

  function onExtract() {
    void runExtract(url.trim(), caption.trim() || undefined);
  }

  // Handle content shared into the app: prefill the fields and auto-extract.
  useEffect(() => {
    const sharedUrl = (params.sharedUrl ?? '').trim();
    const sharedText = (params.sharedText ?? '').trim();
    if (!sharedUrl && !sharedText) return;

    const signature = `${sharedUrl}|${sharedText}`;
    if (handledShareRef.current === signature) return;
    handledShareRef.current = signature;

    const urlFromText = sharedText.match(/https?:\/\/\S+/)?.[0] ?? '';
    const finalUrl = sharedUrl || urlFromText;
    const finalCaption = sharedText && sharedText !== finalUrl ? sharedText : '';

    if (finalUrl) setUrl(finalUrl);
    if (finalCaption) {
      setCaption(finalCaption);
      setShowCaption(true);
    }
    void runExtract(finalUrl, finalCaption || undefined);
    // Only re-run when the shared params change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.sharedUrl, params.sharedText]);

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
        // Over the saved-recipe cap — open the paywall.
        router.push('/paywall');
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
        Paste a link to a TikTok, Reel, or YouTube Short — or share one straight into Social Cook.
        Adding the caption text gives the best results.
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
