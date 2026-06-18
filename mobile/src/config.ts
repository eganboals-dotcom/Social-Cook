/**
 * Mobile runtime configuration.
 *
 * The backend base URL comes from the EXPO_PUBLIC_API_URL env var — Expo inlines
 * any EXPO_PUBLIC_* variable at build time. Defaults to localhost for dev.
 *
 * Reaching a backend running on your computer:
 *   - iOS simulator:    http://localhost:8000
 *   - Android emulator: http://10.0.2.2:8000   (localhost = the emulator itself)
 *   - Physical device:  http://<your-computer-LAN-IP>:8000
 */
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
