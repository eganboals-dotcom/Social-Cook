import { Alert, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';

import * as api from '../../src/api/client';
import { useAuth } from '../../src/auth/AuthContext';
import { Banner } from '../../src/components/Banner';
import { Button } from '../../src/components/Button';
import { Screen } from '../../src/components/Screen';
import { restorePurchases } from '../../src/purchases/purchases';
import { colors, radius, spacing } from '../../src/theme';

export default function SettingsScreen() {
  const { user, signOut, refreshUser } = useAuth();
  const router = useRouter();

  if (user) {
    return (
      <Screen>
        <View style={styles.card}>
          <Text style={styles.label}>SIGNED IN AS</Text>
          <Text style={styles.email}>{user.email}</Text>
          <Text style={styles.meta}>
            {user.saved_recipe_count} of {user.saved_recipe_cap} recipes saved
          </Text>
        </View>
        <Button title="Unlock more recipes" onPress={() => router.push('/paywall')} />
        <Button
          title="Restore purchases"
          variant="secondary"
          onPress={async () => {
            try {
              await restorePurchases();
              await api.validatePurchases();
              await refreshUser();
              Alert.alert('Restore complete', 'Your purchases have been restored.');
            } catch {
              Alert.alert('Restore failed', 'Could not restore purchases right now.');
            }
          }}
        />
        <Button
          title="Log out"
          variant="danger"
          onPress={async () => {
            await signOut();
            router.replace('/(tabs)/add');
          }}
        />
      </Screen>
    );
  }

  return (
    <Screen>
      <Banner tone="info">
        You&apos;re using Social Cook without an account. Sign in to sync your recipes across devices
        and save more.
      </Banner>
      <Button title="Sign in" onPress={() => router.push('/login')} />
      <Button title="Create account" variant="secondary" onPress={() => router.push('/signup')} />
    </Screen>
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
  label: { fontSize: 11, fontWeight: '700', color: colors.muted, letterSpacing: 1 },
  email: { fontSize: 18, fontWeight: '700', color: colors.text, marginTop: spacing(1) },
  meta: { fontSize: 14, color: colors.subtle, marginTop: spacing(2) },
});
