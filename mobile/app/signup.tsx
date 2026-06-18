import { useState } from 'react';
import { StyleSheet, Text } from 'react-native';
import { Link, useRouter } from 'expo-router';

import { ApiError } from '../src/api/client';
import { useAuth } from '../src/auth/AuthContext';
import { Banner } from '../src/components/Banner';
import { Button } from '../src/components/Button';
import { Screen } from '../src/components/Screen';
import { TextField } from '../src/components/TextField';
import { colors, spacing } from '../src/theme';

export default function SignupScreen() {
  const { signUp } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    setError(null);
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    setLoading(true);
    try {
      await signUp(email.trim(), password);
      router.replace('/(tabs)/recipes');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not create your account.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen scroll>
      <TextField
        label="Email"
        value={email}
        onChangeText={setEmail}
        placeholder="you@example.com"
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="email-address"
      />
      <TextField
        label="Password"
        value={password}
        onChangeText={setPassword}
        placeholder="At least 8 characters"
        secureTextEntry
      />
      {error ? <Banner tone="danger">{error}</Banner> : null}
      <Button title="Create account" onPress={onSubmit} loading={loading} />
      <Banner tone="info">
        Have recipes saved on this device? They&apos;ll move into your new account automatically.
      </Banner>
      <Link href="/login" asChild>
        <Text style={styles.link}>Already have an account? Sign in</Text>
      </Link>
    </Screen>
  );
}

const styles = StyleSheet.create({
  link: { color: colors.accent, fontWeight: '600', textAlign: 'center', paddingVertical: spacing(2) },
});
