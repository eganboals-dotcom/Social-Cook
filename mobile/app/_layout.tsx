import { useEffect } from 'react';
import { Stack, useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ShareIntentProvider, useShareIntentContext } from 'expo-share-intent';

import { AuthProvider } from '../src/auth/AuthContext';
import { colors } from '../src/theme';

/**
 * Routes content shared into the app (via the OS share sheet) to the Add
 * screen, pre-filled, so extraction can start immediately. Rendered inside
 * ShareIntentProvider so it can read the share context.
 */
function ShareIntentRouter() {
  const router = useRouter();
  const { hasShareIntent, shareIntent, resetShareIntent } = useShareIntentContext();

  useEffect(() => {
    if (!hasShareIntent) return;
    router.push({
      pathname: '/(tabs)/add',
      params: { sharedUrl: shareIntent.webUrl ?? '', sharedText: shareIntent.text ?? '' },
    });
    resetShareIntent();
    // Only react to a new share intent arriving.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasShareIntent]);

  return null;
}

export default function RootLayout() {
  return (
    <ShareIntentProvider>
      <SafeAreaProvider>
        <AuthProvider>
          <StatusBar style="dark" />
          <ShareIntentRouter />
          <Stack
            screenOptions={{
              headerStyle: { backgroundColor: colors.bg },
              headerShadowVisible: false,
              headerTintColor: colors.text,
              headerTitleStyle: { color: colors.text },
              contentStyle: { backgroundColor: colors.bg },
            }}
          >
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
            <Stack.Screen name="login" options={{ title: 'Sign in', presentation: 'modal' }} />
            <Stack.Screen name="signup" options={{ title: 'Create account', presentation: 'modal' }} />
            <Stack.Screen
              name="forgot-password"
              options={{ title: 'Reset password', presentation: 'modal' }}
            />
            <Stack.Screen name="recipe/[id]" options={{ title: 'Recipe' }} />
          </Stack>
        </AuthProvider>
      </SafeAreaProvider>
    </ShareIntentProvider>
  );
}
