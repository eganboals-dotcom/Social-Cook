# Social Cook — Mobile (Expo)

Cross-platform iOS + Android app built with React Native + Expo (TypeScript),
using **expo-router** for navigation.

## Run

```bash
cd mobile
npm install
npx expo install         # align native modules to your installed SDK (needs network)
cp .env.example .env      # point EXPO_PUBLIC_API_URL at your backend
npm start                 # then press i (iOS), a (Android), or w (web)
```

Make sure the backend is running first (see the root `README.md`). On the
Android emulator set `EXPO_PUBLIC_API_URL=http://10.0.2.2:8000`; on a physical
device use your computer's LAN IP.

> Dependency versions in `package.json` were resolved against **Expo SDK 56**. If
> you change the SDK, run `npx expo install --fix` to realign the native modules.

## Structure

```
mobile/
├── app/                        # expo-router routes
│   ├── _layout.tsx             # root: AuthProvider + Stack
│   ├── index.tsx               # redirect → (tabs)/add
│   ├── (tabs)/                 # Add · My recipes · Settings
│   │   ├── add.tsx             # paste link → /extract → preview → save
│   │   ├── recipes.tsx         # list/search + "X of Y saved"
│   │   └── settings.tsx        # account, sign in / out
│   ├── recipe/[id].tsx         # view + edit + delete a recipe
│   ├── login.tsx · signup.tsx · forgot-password.tsx
├── src/
│   ├── api/client.ts           # typed backend client (auth header injected)
│   ├── auth/AuthContext.tsx    # JWT (secure-store) + local-first migration
│   ├── storage/localRecipes.ts # AsyncStorage local-first store
│   ├── components/             # Button, TextField, Screen, RecipeView, ...
│   ├── theme.ts · types.ts · config.ts
└── assets/                     # icons / splash
```

## How it fits together

- **Local-first:** before signing in, extracted recipes are saved on the device
  (AsyncStorage). On sign-up/login they migrate into the account via
  `POST /recipes/import`, then are cleared.
- **Auth:** the JWT lives in `expo-secure-store` and is re-applied to the API
  client on launch; signing out clears it.
- **Cap:** saving past the limit returns `402`; the app surfaces the message
  (the full paywall / in-app-purchase flow lands in Phase 5).

The share-target config plugin (share a post straight into the app) lands in
Phase 4.
