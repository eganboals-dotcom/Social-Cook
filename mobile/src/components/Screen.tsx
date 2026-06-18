import type { ReactNode } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { colors, spacing } from '../theme';

/** Screen container with consistent padding + keyboard handling. */
export function Screen({ children, scroll = false }: { children: ReactNode; scroll?: boolean }) {
  const insets = useSafeAreaInsets();
  const pad = { paddingBottom: insets.bottom + spacing(4) };

  if (scroll) {
    return (
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          style={styles.flex}
          contentContainerStyle={[styles.content, pad]}
          keyboardShouldPersistTaps="handled"
        >
          {children}
        </ScrollView>
      </KeyboardAvoidingView>
    );
  }
  return <View style={[styles.flex, styles.content, pad]}>{children}</View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing(5), gap: spacing(3) },
});
