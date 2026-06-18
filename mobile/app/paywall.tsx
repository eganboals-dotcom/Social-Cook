import { useEffect, useState } from 'react';
import { StyleSheet, Text } from 'react-native';
import { useRouter } from 'expo-router';

import * as api from '../src/api/client';
import { ApiError } from '../src/api/client';
import { useAuth } from '../src/auth/AuthContext';
import { Banner } from '../src/components/Banner';
import { Button } from '../src/components/Button';
import { Screen } from '../src/components/Screen';
import {
  getUnlockPackage,
  isPurchasesAvailable,
  purchaseUnlock,
  restorePurchases,
} from '../src/purchases/purchases';
import { colors, spacing } from '../src/theme';

export default function PaywallScreen() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();
  const [price, setPrice] = useState(10);
  const [increment, setIncrement] = useState(25);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const cfg = await api.getUnlockConfig();
        setPrice(cfg.unlock_price_usd);
        setIncrement(cfg.cap_increment);
      } catch {
        // keep defaults
      }
    })();
  }, []);

  async function onBuy() {
    setError(null);
    if (!isPurchasesAvailable()) {
      setError(
        'In-app purchases aren’t available in this build. Use a dev/production build with RevenueCat configured.',
      );
      return;
    }
    setBusy(true);
    try {
      const pkg = await getUnlockPackage();
      if (!pkg) {
        setError('No unlock product is available right now.');
        return;
      }
      const purchased = await purchaseUnlock(pkg);
      if (!purchased) return; // user cancelled
      await api.validatePurchases(); // server validates the receipt + raises the cap
      await refreshUser();
      router.back();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Purchase failed. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  async function onRestore() {
    setError(null);
    setBusy(true);
    try {
      await restorePurchases();
      await api.validatePurchases();
      await refreshUser();
      router.back();
    } catch {
      setError('Could not restore purchases right now.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen>
      <Text style={styles.title}>Unlock more recipes</Text>
      {user ? (
        <Text style={styles.body}>
          You&apos;ve saved {user.saved_recipe_count} of {user.saved_recipe_cap}. Unlock {increment}{' '}
          more for ${price}.
        </Text>
      ) : (
        <Text style={styles.body}>Unlock {increment} more saved recipes for ${price}.</Text>
      )}
      {error ? <Banner tone="danger">{error}</Banner> : null}
      <Button title={`Unlock ${increment} more — $${price}`} onPress={onBuy} loading={busy} />
      <Button title="Restore purchases" variant="secondary" onPress={onRestore} />
      <Text style={styles.fine}>
        Processed by the App Store / Google Play and validated on our server.
      </Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 24, fontWeight: '800', color: colors.text },
  body: { fontSize: 16, color: colors.subtle, lineHeight: 22, marginBottom: spacing(2) },
  fine: { fontSize: 12, color: colors.muted, textAlign: 'center', marginTop: spacing(2) },
});
