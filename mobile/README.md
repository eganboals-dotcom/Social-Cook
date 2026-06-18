# Social Cook — Mobile (Expo)

Cross-platform iOS + Android app built with React Native + Expo (TypeScript).

## Run

```bash
cd mobile
npm install
cp .env.example .env        # point EXPO_PUBLIC_API_URL at your backend
npm start                   # then press i (iOS), a (Android), or w (web)
```

Make sure the backend is running first (see the root `README.md`). On the
Android emulator, set `EXPO_PUBLIC_API_URL=http://10.0.2.2:8000`; on a physical
device, use your computer's LAN IP.

## Structure

```
mobile/
├── App.tsx          # root component (Phase 0 landing + backend health check)
├── index.ts         # Expo entry point
├── src/
│   ├── config.ts    # runtime config (API base URL from EXPO_PUBLIC_API_URL)
│   └── api/
│       └── client.ts  # typed backend client
└── assets/          # icons / splash
```

Screens (auth, add-recipe, recipe view, my-recipes, paywall, settings) and the
share-target config plugin are added in Phases 3–5.
