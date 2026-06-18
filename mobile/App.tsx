import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';

import { API_BASE_URL } from './src/config';
import { checkHealth } from './src/api/client';

type Status = 'idle' | 'loading' | 'ok' | 'error';

// Phase 0 landing screen: branding + a quick check that the app can reach the
// backend. Real screens (auth, add-recipe, my-recipes) arrive in Phase 3.
export default function App() {
  const [status, setStatus] = useState<Status>('idle');
  const [detail, setDetail] = useState('');

  async function onCheck() {
    setStatus('loading');
    setDetail('');
    try {
      const res = await checkHealth();
      setStatus('ok');
      setDetail(`Connected · ${res.status}`);
    } catch (e) {
      setStatus('error');
      setDetail(e instanceof Error ? e.message : 'Unknown error');
    }
  }

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />
      <Text style={styles.emoji}>🍳</Text>
      <Text style={styles.title}>Social Cook</Text>
      <Text style={styles.subtitle}>
        Turn social cooking videos into clean, structured recipes.
      </Text>

      <View style={styles.card}>
        <Text style={styles.cardLabel}>BACKEND</Text>
        <Text style={styles.url}>{API_BASE_URL}</Text>

        <Pressable
          style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
          onPress={onCheck}
          disabled={status === 'loading'}
        >
          {status === 'loading' ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Test connection</Text>
          )}
        </Pressable>

        {(status === 'ok' || status === 'error') && (
          <Text style={[styles.status, status === 'ok' ? styles.ok : styles.error]}>
            {status === 'ok' ? '✓ ' : '✗ '}
            {detail}
          </Text>
        )}
      </View>

      <Text style={styles.phase}>Phase 0 · skeleton</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFF8F2',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 28,
  },
  emoji: { fontSize: 56, marginBottom: 8 },
  title: { fontSize: 32, fontWeight: '800', color: '#1F2937' },
  subtitle: {
    fontSize: 15,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 32,
  },
  card: {
    width: '100%',
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
  },
  cardLabel: { fontSize: 11, fontWeight: '700', color: '#9CA3AF', letterSpacing: 1 },
  url: { fontSize: 14, color: '#374151', marginTop: 4, marginBottom: 16 },
  button: {
    backgroundColor: '#EF5B2B',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  buttonPressed: { opacity: 0.85 },
  buttonText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  status: { marginTop: 14, fontSize: 14, fontWeight: '600' },
  ok: { color: '#15803D' },
  error: { color: '#B91C1C' },
  phase: { position: 'absolute', bottom: 40, color: '#C4B7AC', fontSize: 12 },
});
