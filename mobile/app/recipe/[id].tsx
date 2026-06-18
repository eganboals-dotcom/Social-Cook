import { useCallback, useState } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Stack, useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import * as api from '../../src/api/client';
import { ApiError } from '../../src/api/client';
import { Button } from '../../src/components/Button';
import { deleteLocalRecipe, getLocalRecipe, updateLocalRecipe } from '../../src/storage/localRecipes';
import { colors, radius, spacing } from '../../src/theme';
import type { Ingredient, RecipeCreate, Step } from '../../src/types';

export default function RecipeDetailScreen() {
  const { id, local } = useLocalSearchParams<{ id: string; local?: string }>();
  const isLocal = local === '1';
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [saving, setSaving] = useState(false);
  const [title, setTitle] = useState('');
  const [servings, setServings] = useState('');
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [steps, setSteps] = useState<Step[]>([]);

  const hydrate = useCallback(
    (r: { title: string; servings?: string | null; ingredients: Ingredient[]; steps: Step[] }) => {
      setTitle(r.title);
      setServings(r.servings ?? '');
      setIngredients(r.ingredients.map((i) => ({ ...i })));
      setSteps(r.steps.map((s) => ({ ...s })));
    },
    [],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setNotFound(false);
    try {
      if (isLocal) {
        const r = await getLocalRecipe(String(id));
        if (!r) {
          setNotFound(true);
          return;
        }
        hydrate(r);
      } else {
        hydrate(await api.getRecipe(Number(id)));
      }
    } catch {
      setNotFound(true);
    } finally {
      setLoading(false);
    }
  }, [id, isLocal, hydrate]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  function setIngredient(index: number, patch: Partial<Ingredient>) {
    setIngredients((prev) => prev.map((ing, i) => (i === index ? { ...ing, ...patch } : ing)));
  }

  function setStepText(index: number, text: string) {
    setSteps((prev) => prev.map((s, i) => (i === index ? { ...s, text } : s)));
  }

  async function onSave() {
    const cleanIngredients = ingredients
      .filter((i) => i.name.trim())
      .map((i) => ({
        name: i.name.trim(),
        amount: (i.amount ?? '').trim() || null,
        unit: (i.unit ?? '').trim() || null,
      }));
    const cleanSteps = steps
      .filter((s) => s.text.trim())
      .map((s, i) => ({ order: i + 1, text: s.text.trim() }));

    if (!title.trim()) {
      Alert.alert('Add a title', 'Your recipe needs a title.');
      return;
    }
    if (cleanIngredients.length === 0 || cleanSteps.length === 0) {
      Alert.alert('Incomplete recipe', 'Add at least one ingredient and one step.');
      return;
    }

    const patch: Partial<RecipeCreate> = {
      title: title.trim(),
      servings: servings.trim() || null,
      ingredients: cleanIngredients,
      steps: cleanSteps,
    };

    setSaving(true);
    try {
      if (isLocal) await updateLocalRecipe(String(id), patch);
      else await api.updateRecipe(Number(id), patch);
      router.back();
    } catch (e) {
      Alert.alert('Could not save', e instanceof ApiError ? e.message : 'Please try again.');
    } finally {
      setSaving(false);
    }
  }

  function onDelete() {
    Alert.alert('Delete recipe', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            if (isLocal) await deleteLocalRecipe(String(id));
            else await api.deleteRecipe(Number(id));
            router.back();
          } catch (e) {
            Alert.alert('Could not delete', e instanceof ApiError ? e.message : 'Please try again.');
          }
        },
      },
    ]);
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <Text style={styles.dim}>Loading…</Text>
      </View>
    );
  }
  if (notFound) {
    return (
      <View style={styles.center}>
        <Text style={styles.dim}>Recipe not found.</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <Stack.Screen options={{ title: 'Edit recipe' }} />
      <ScrollView
        contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + spacing(8) }]}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.fieldLabel}>Title</Text>
        <TextInput
          style={styles.input}
          value={title}
          onChangeText={setTitle}
          placeholder="Recipe title"
          placeholderTextColor={colors.muted}
        />

        <Text style={styles.fieldLabel}>Servings</Text>
        <TextInput
          style={styles.input}
          value={servings}
          onChangeText={setServings}
          placeholder="e.g. 2"
          placeholderTextColor={colors.muted}
        />

        <Text style={styles.section}>Ingredients</Text>
        {ingredients.map((ing, i) => (
          <View key={`ing-${i}`} style={styles.row}>
            <TextInput
              style={[styles.cell, styles.amt]}
              value={ing.amount ?? ''}
              onChangeText={(t) => setIngredient(i, { amount: t })}
              placeholder="amt"
              placeholderTextColor={colors.muted}
            />
            <TextInput
              style={[styles.cell, styles.unit]}
              value={ing.unit ?? ''}
              onChangeText={(t) => setIngredient(i, { unit: t })}
              placeholder="unit"
              placeholderTextColor={colors.muted}
            />
            <TextInput
              style={[styles.cell, styles.name]}
              value={ing.name}
              onChangeText={(t) => setIngredient(i, { name: t })}
              placeholder="ingredient"
              placeholderTextColor={colors.muted}
            />
            <Pressable
              onPress={() => setIngredients((prev) => prev.filter((_, idx) => idx !== i))}
              style={styles.remove}
            >
              <Text style={styles.removeText}>✕</Text>
            </Pressable>
          </View>
        ))}
        <Button
          title="+ Add ingredient"
          variant="secondary"
          onPress={() => setIngredients((prev) => [...prev, { name: '', amount: '', unit: '' }])}
        />

        <Text style={styles.section}>Steps</Text>
        {steps.map((step, i) => (
          <View key={`step-${i}`} style={styles.row}>
            <Text style={styles.stepNum}>{i + 1}.</Text>
            <TextInput
              style={[styles.cell, styles.step]}
              value={step.text}
              onChangeText={(t) => setStepText(i, t)}
              placeholder="Describe this step"
              placeholderTextColor={colors.muted}
              multiline
            />
            <Pressable
              onPress={() =>
                setSteps((prev) =>
                  prev
                    .filter((_, idx) => idx !== i)
                    .map((s, idx) => ({ ...s, order: idx + 1 })),
                )
              }
              style={styles.remove}
            >
              <Text style={styles.removeText}>✕</Text>
            </Pressable>
          </View>
        ))}
        <Button
          title="+ Add step"
          variant="secondary"
          onPress={() => setSteps((prev) => [...prev, { order: prev.length + 1, text: '' }])}
        />

        <View style={styles.spacer} />
        <Button title="Save changes" onPress={onSave} loading={saving} />
        <Button title="Delete recipe" variant="danger" onPress={onDelete} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, backgroundColor: colors.bg, alignItems: 'center', justifyContent: 'center' },
  dim: { color: colors.subtle, fontSize: 15 },
  content: { padding: spacing(5), gap: spacing(2) },
  fieldLabel: { fontSize: 13, fontWeight: '600', color: colors.subtle, marginTop: spacing(2) },
  section: { fontSize: 16, fontWeight: '800', color: colors.text, marginTop: spacing(4) },
  input: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing(3.5),
    paddingVertical: spacing(3),
    fontSize: 16,
    color: colors.text,
  },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing(2) },
  cell: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    paddingHorizontal: spacing(2.5),
    paddingVertical: spacing(2.5),
    fontSize: 15,
    color: colors.text,
  },
  amt: { width: 52 },
  unit: { width: 64 },
  name: { flex: 1 },
  step: { flex: 1, minHeight: 44 },
  stepNum: { width: 22, fontSize: 15, fontWeight: '700', color: colors.subtle },
  remove: { paddingHorizontal: spacing(1.5), paddingVertical: spacing(2) },
  removeText: { color: colors.muted, fontSize: 16 },
  spacer: { height: spacing(2) },
});
