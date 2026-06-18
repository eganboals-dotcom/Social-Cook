# 🍳 Social Cook

Paste or **share** a link to a cooking video from TikTok, Instagram Reels, or
YouTube Shorts and get back a clean, structured recipe — title, servings,
ingredient list, and numbered steps — saved to your account.

> **Status:** v1 complete (Phases 0–6) — extraction, accounts, mobile app, share
> sheet, monetization, and a polish pass. See the [roadmap](#build-roadmap) below.

---

## How recipe extraction works

Turning a video into a recipe combines up to three signals, **cheapest and
highest-value first**, then hands them to an LLM that returns structured JSON
which we **validate before saving** (never trust raw model output):

1. **Caption / description text** — often contains the whole recipe. Always tried first.
2. **Spoken audio** — transcribed with a Whisper-class model. _Best-effort._
3. **On-screen text / frames** — a few sampled frames read by a vision LLM.
   _Most expensive/slowest — optional, only when caption + audio fall short._

### ⚠️ A note on getting the video (Terms of Service)

The major platforms **do not** offer official APIs to download a video by link,
and scraping their video files generally violates their Terms of Service. We
design around this:

- **Primary path:** the native **share sheet** — users share a post _into_ our
  app, so we don't fetch anything (Phase 4).
- We lean heavily on **caption text**, which frequently contains the full recipe.
- Full video/audio download is a **best-effort enhancement** behind a pluggable
  `VideoIngest` interface, so implementations can be swapped without touching the
  rest of the app.
- Anywhere the approach depends on platform ToS is flagged with a `ToS:` comment
  in the code (see `backend/app/extraction/base.py`).

---

## Tech stack

| Layer        | Choice                                                              |
| ------------ | ------------------------------------------------------------------ |
| Mobile       | React Native + **Expo** (TypeScript), iOS + Android                |
| Backend      | **Python + FastAPI**, REST                                         |
| LLM          | **Anthropic API** — `claude-sonnet-4-6` (recipe structuring + vision) |
| Transcription| **OpenAI Whisper API** (`whisper-1`), behind a pluggable `Transcriber` |
| Database     | **PostgreSQL** (SQLAlchemy + Alembic)                              |
| Auth         | Email + password (argon2 hashing via passlib), JWT tokens          |
| Payments     | **RevenueCat** wrapping App Store + Google Play in-app purchases   |

---

## Repository layout

```
Social-Cook/
├── README.md
├── .env.example                  # backend env template → copy to backend/.env
├── .gitignore
├── backend/                      # FastAPI service
│   ├── app/
│   │   ├── main.py               # app wiring, CORS, routers
│   │   ├── config.py             # env-driven settings (no hard-coded secrets)
│   │   ├── api/health.py         # /health, /
│   │   ├── schemas/recipe.py     # validated recipe contract (LLM output)
│   │   ├── extraction/           # VideoIngest / Transcriber / VisionReader + pipeline
│   │   └── monetization/config.py# the "25 recipes per $10" config (single source of truth)
│   ├── tests/                    # pytest
│   ├── requirements.txt          # dependency floors
│   ├── requirements.lock.txt     # exact pinned versions
│   └── pytest.ini
└── mobile/                       # Expo app (see mobile/README.md)
```

---

## Running locally

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 14+ (only needed from Phase 2 onward)
- API keys: **Anthropic** (recipe structuring/vision) and **OpenAI** (Whisper).
  Get them from the respective dashboards and put them in `backend/.env`.

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # or requirements.lock.txt for exact pins
cp ../.env.example .env                 # then fill in ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.
alembic upgrade head                     # create the DB schema (needs Postgres running)
uvicorn app.main:app --reload --port 8000
```

Verify: <http://localhost:8000/health> → `{"status":"ok"}`.
Interactive API docs: <http://localhost:8000/docs>.

Run the checks:

```bash
cd backend && source .venv/bin/activate
pytest          # 40 tests
ruff check .    # lint
```

The mobile app is typechecked with `cd mobile && npx tsc --noEmit`.

### Mobile

```bash
cd mobile
npm install
cp .env.example .env                    # point EXPO_PUBLIC_API_URL at your backend
npm start                               # press i / a / w for iOS / Android / web
```

See [`mobile/README.md`](mobile/README.md) for emulator/device networking notes.

---

## Recipe extraction (Phase 1)

`POST /extract` turns a URL + optional caption into a validated recipe. It runs
caption-first, with optional audio (Whisper) and vision (Claude) signals behind
the pluggable `VideoIngest` / `Transcriber` / `VisionReader` interfaces. The LLM
returns structured JSON (via Anthropic structured outputs) which is validated
against a strict pydantic contract before it's returned — raw model output is
never trusted.

```bash
curl -s localhost:8000/extract \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://www.tiktok.com/@chef/video/123",
    "caption": "Garlic butter pasta — 200g spaghetti, 4 cloves garlic, 3 tbsp butter... 1) boil pasta 2) fry garlic 3) toss in parmesan"
  }' | jq
```

Response shape: `{ recipe: {title, servings, ingredients[], steps[]}, source_platform, raw_extraction }`.
A post with no usable recipe returns a friendly `422` ("couldn't find a recipe"),
not a crash.

Try it from a script (no UI needed):

```bash
cd backend && source .venv/bin/activate
python -m scripts.extract_demo                          # built-in sample caption
python -m scripts.extract_demo --url <url> --caption "<caption>"
```

This requires `ANTHROPIC_API_KEY` in `backend/.env`. `use_audio` / `use_vision`
are accepted but only do work once a provider supplies media (best-effort; the
default share-sheet path does not download media — see the ToS note above).

## Accounts & data

- Email + password accounts: sign-up, log-in, log-out, email password reset.
- Passwords are stored only as **argon2 salted hashes** — never plaintext.
- **Local-first saving:** users can save a few recipes on-device before creating
  an account; those recipes **migrate into the account on sign-up**.
- Each saved recipe belongs to a user and syncs across devices/re-logins.

### Data model (starting point)

- **User**: `id`, `email` (unique), `password_hash`, `created_at`, `saved_recipe_cap` (default 25).
- **Recipe**: `id`, `user_id`, `source_url`, `source_platform`, `title`, `servings`,
  `ingredients` (JSON `[{name, amount, unit}]`), `steps` (JSON `[{order, text}]`),
  `created_at`, `raw_extraction` (JSON: caption/transcript used, for debugging).
- **Purchase**: `id`, `user_id`, `platform`, `product_id`, `transaction_id`, `validated_at`, `cap_added`.

**Duplicate `source_url`:** we will _not_ add a hard unique constraint. Instead,
re-adding a URL a user already saved surfaces a "you already saved this" notice
and offers to open the existing recipe — re-extraction is sometimes wanted.

---

### Auth & recipe endpoints (Phase 2)

Recipe endpoints require an `Authorization: Bearer <token>` header (from signup/login).

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/auth/signup` | Create account → JWT + user |
| POST | `/auth/login` | Log in → JWT + user |
| POST | `/auth/logout` | Acknowledge logout (JWT discarded client-side) |
| POST | `/auth/forgot-password` | Email a reset link (dev: logged to console) |
| POST | `/auth/reset-password` | Set a new password from a reset token |
| GET | `/auth/me` | Current user + saved count/cap |
| POST | `/recipes` | Save a recipe (cap-checked; soft-dedupes by URL) |
| GET | `/recipes?q=` | List/search the user's recipes + "X of Y saved" |
| GET / PATCH / DELETE | `/recipes/{id}` | View / edit / delete one recipe |
| POST | `/recipes/import` | Bulk-import local recipes (migration on sign-up) |

Passwords are **argon2**-hashed; auth endpoints are **rate-limited** (slowapi).
Saving past the cap returns **`402`** with `{saved_recipe_count, saved_recipe_cap}`
so the client can open the paywall. Schema is managed with **Alembic**. Password
reset emails are logged by a console sender in dev — swap in a real provider via
`app/email.py` for production.

## Monetization (freemium)

- **25 recipes free.** Each additional **$10** unlock raises the cap by 25
  (25 → 50 → 75 → …).
- The unlock is a **consumable** in-app purchase (repeatable), sold via
  **RevenueCat** over App Store + Google Play. Outside payment processors are not
  allowed by Apple/Google for unlocking digital content.
- On purchase, the receipt is **validated server-side** before the cap is raised
  — the client is never trusted. The server's record of validated purchases is
  the source of truth for a user's cap (so it survives reinstall/new device).
- The "25 per $10" numbers live in **one config**:
  `backend/app/monetization/config.py`.

> Note: Apple/Google take ~15–30% of each $10. Selling access outside the app
> (e.g. web purchase) would avoid the cut but has its own rules — out of scope for v1.

### Endpoints & flow (Phase 5)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/purchases/config` | The unlock numbers (price / increment / product id) — paywall reads these |
| POST | `/purchases/webhook` | RevenueCat → server (shared-secret auth); **authoritative** crediting |
| POST | `/purchases/validate` | Client-driven validate + **restore**: reconciles against RevenueCat's REST API |
| GET | `/purchases` | The user's purchase history |

Crediting is **idempotent** on the store `transaction_id` (plus a unique DB
constraint), so the webhook and validate paths can't double-credit. The mobile
paywall (`app/paywall.tsx`) opens on a `402`, runs the RevenueCat purchase behind
a wrapper, then calls `/purchases/validate`.

**To actually transact** you need: a RevenueCat account with the `recipe_unlock_25`
consumable configured for App Store + Google Play, the public SDK keys in
`mobile/.env` (`EXPO_PUBLIC_REVENUECAT_*`), the REST key + webhook secret in
`backend/.env` (`REVENUECAT_API_KEY` / `REVENUECAT_WEBHOOK_AUTH`), and a dev/prod
build (IAP doesn't run in Expo Go). Without keys, the app still runs and the
paywall shows — it just can't complete a purchase.

---

## Secrets

All secrets live in environment variables — **never commit API keys**. Copy
`.env.example` → `backend/.env` and fill it in. The `.env` files are gitignored.

---

## Build roadmap

- [x] **Phase 0 — Setup:** repo structure, FastAPI skeleton, Expo skeleton, `.env.example`, README.
- [x] **Phase 1 — Extraction core:** `/extract` endpoint; caption + optional audio/vision → validated JSON via the LLM; testable from a script.
- [x] **Phase 2 — Accounts:** sign-up / log-in / log-out / password reset; JWT; recipes tied to users; local-first migration.
- [x] **Phase 3 — Mobile app:** add-recipe, recipe view, my-recipes; wired to the backend.
- [x] **Phase 4 — Share sheet:** register as a share target on iOS + Android.
- [x] **Phase 5 — Monetization:** cap tracking, paywall, RevenueCat IAP, server-side receipt validation, restore purchases.
- [x] **Phase 6 — Polish:** error/empty/loading states, search, tests for extraction + cap logic.
