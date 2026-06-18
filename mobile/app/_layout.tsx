import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AuthProvider } from '../src/auth/AuthContext';
import { colors } from '../src/theme';

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <StatusBar style="dark" />
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
  );
}
