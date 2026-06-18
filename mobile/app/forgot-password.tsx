import { useState } from 'react';
import { useAuth } from '../src/auth/AuthContext';
import { Banner } from '../src/components/Banner';
import { Button } from '../src/components/Button';
import { Screen } from '../src/components/Screen';
import { TextField } from '../src/components/TextField';

export default function ForgotPasswordScreen() {
  const { forgotPassword } = useAuth();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    setError(null);
    setMessage(null);
    setLoading(true);
    try {
      setMessage(await forgotPassword(email.trim()));
    } catch {
      setError('Could not send a reset link. Please try again.');
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
      {message ? <Banner tone="ok">{message}</Banner> : null}
      {error ? <Banner tone="danger">{error}</Banner> : null}
      <Button title="Send reset link" onPress={onSubmit} loading={loading} />
    </Screen>
  );
}
