import { StyleSheet, Text, View } from 'react-native';

import { colors, radius, spacing } from '../theme';
import type { Ingredient, Step } from '../types';

/** Read-only display of a recipe (used in the extraction preview). */
export function RecipeView({
  title,
  servings,
  ingredients,
  steps,
}: {
  title: string;
  servings?: string | null;
  ingredients: Ingredient[];
  steps: Step[];
}) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      {servings ? <Text style={styles.meta}>{servings}</Text> : null}

      <Text style={styles.heading}>Ingredients</Text>
      {ingredients.map((ing, i) => (
        <Text key={`ing-${i}`} style={styles.item}>
          {'•'} {[ing.amount, ing.unit, ing.name].filter(Boolean).join(' ')}
        </Text>
      ))}

      <Text style={styles.heading}>Steps</Text>
      {steps.map((step, i) => (
        <Text key={`step-${i}`} style={styles.item}>
          {step.order}. {step.text}
        </Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    padding: spacing(4),
    borderWidth: 1,
    borderColor: colors.border,
  },
  title: { fontSize: 20, fontWeight: '800', color: colors.text },
  meta: { fontSize: 13, color: colors.subtle, marginTop: spacing(1) },
  heading: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
    marginTop: spacing(4),
    marginBottom: spacing(1),
  },
  item: { fontSize: 15, color: colors.text, lineHeight: 22 },
});
