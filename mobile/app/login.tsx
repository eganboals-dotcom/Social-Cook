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

export default function LoginScreen() {
  const { signIn } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    setError(null);
    setLoading(true);
    try {
      await signIn(email.trim(), password);
      router.replace('/(tabs)/recipes');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not sign in.');
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
        placeholder="••••••••"
        secureTextEntry
      />
      {error ? <Banner tone="danger">{error}</Banner> : null}
      <Button title="Sign in" onPress={onSubmit} loading={loading} />
      <Link href="/forgot-password" asChild>
        <Text style={styles.link}>Forgot your password?</Text>
      </Link>
      <Link href="/signup" asChild>
        <Text style={styles.link}>New here? Create an account</Text>
      </Link>
    </Screen>
  );
}

const styles = StyleSheet.create({
  link: { color: colors.accent, fontWeight: '600', textAlign: 'center', paddingVertical: spacing(2) },
});
