# Nuxt Minimal Starter

Look at the [Nuxt documentation](https://nuxt.com/docs/getting-started/introduction) to learn more.

## Setup

Make sure to install dependencies:

```bash
# npm
npm install

# pnpm
pnpm install

# yarn
yarn install

# bun
bun install
```

## Development Server

Start the development server on `http://localhost:3000`:

```bash
# npm
npm run dev

# pnpm
pnpm dev

# yarn
yarn dev

# bun
bun run dev
```

## Production

Build the application for production:

```bash
# npm
npm run build

# pnpm
pnpm build

# yarn
yarn build

# bun
bun run build
```

Locally preview production build:

```bash
# npm
npm run preview

# pnpm
pnpm preview

# yarn
yarn preview

# bun
bun run preview
```

Check out the [deployment documentation](https://nuxt.com/docs/getting-started/deployment) for more information.

## Web Player Improvements Checklist

### High Priority

- [ ] Move backend player state from global in-memory variables to per-session/per-user scope. (`backend/main.py:35`, `backend/main.py:36`, `backend/main.py:37`)
- [ ] Remove expensive playlist generation and analysis from `/api/play`; precompute in background and cache results. (`backend/main.py:117`, `backend/main.py:122`, `backend/Core/CreateListOfSongs.py:24`, `backend/Core/CreateListOfSongs.py:36`, `backend/Core/CreateListOfSongs.py:46`)
- [ ] Add concurrency guards for `/api/play/next` and `/api/play/previous` to avoid race conditions during rapid transitions. (`backend/main.py:143`, `backend/main.py:150`, `backend/main.py:155`, `backend/main.py:162`)
- [ ] Add frontend error UI (not only console logs), retry actions, and disable controls while requests are in flight. (`frontend/pages/index.vue:115`, `frontend/pages/index.vue:149`, `frontend/pages/index.vue:191`, `frontend/pages/index.vue:197`)
- [ ] Replace 100ms progress polling with event-driven updates (`timeupdate` + targeted `requestAnimationFrame` during scrubbing). (`frontend/composables/useDualDeckPlayer.ts:173`, `frontend/composables/useDualDeckPlayer.ts:248`)

### Medium Priority

- [ ] Render album art from backend `coverUrl` with fallback image only when cover data is unavailable. (`frontend/pages/index.vue:45`, `frontend/pages/index.vue:47`, `backend/main.py:71`)
- [ ] Clean up frontend component contract mismatches (unused props/events, enforce explicit props/emits). (`frontend/pages/index.vue:9`, `frontend/components/AudioPlayerShell.vue:49`, `frontend/components/AudioPlayerShell.vue:64`)
- [ ] Add typed API request/response schemas (Pydantic in backend + matching TypeScript types in frontend). (`backend/main.py:9`, `backend/main.py:64`, `frontend/pages/index.vue:136`)
- [ ] Move backend API base/proxy target to environment-based runtime config for dev/staging/prod. (`frontend/nuxt.config.ts:9`)

### Nice to Have

- [ ] Improve transition UX: show loading/buffering state, queued-track indication, and clearer overlap handoff feedback. (`frontend/pages/index.vue:154`, `frontend/pages/index.vue:178`, `frontend/components/AudioPlayerShell.vue:37`)
