# Project: Customer Support Dashboard

## What This Is
A 2-page internal web app for customer support training.
- Page 1: Dashboard — call analytics from SmartFlo TTS API
- Page 2: Transcript Analytics — AI-powered call analysis via Google Gemini 2.0 Flash

## Tech Stack
- Backend: Python 3.11, FastAPI, deployed on Render
- Frontend: React 18, TypeScript, Vite, TanStack Query, Recharts, shadcn/ui, Tailwind CSS, deployed on Vercel
- External APIs: SmartFlo TTS (call logs + recordings), Google Gemini 2.0 Flash (audio analysis)

## Key Files to Read First
- docs/TECHNICAL_SPEC.md — full architecture, endpoints, schemas, phases
- docs/tts_api_reference.md — SmartFlo API endpoints we use
- docs/gemini_api_notes.md — Gemini audio input pattern

## Directory Conventions
- All backend code in /backend
- All frontend code in /frontend
- Never put credentials in code — use .env files
- TTS credentials live in backend/.env only (never frontend)

## Current Phase
Phase 2 complete — Full app built and deployed (backend on Render, frontend on Vercel)
Both pages working locally. Gemini analyze endpoints pending valid API key test.

## Important Constraints
1. TTS auth token expires every 3600s — must auto-refresh
2. Recording URLs are short-lived — download immediately, don't cache
3. Gemini handles Hindi, Kannada, Telugu, Tamil, Malayalam, Marathi, English + code-switching
4. All TTS API calls must be proxied through our backend — never called from frontend
5. CORS: in production only allow VITE_API_BASE_URL origin

## Environment Variables Needed
### backend/.env
TTS_EMAIL=
TTS_PASSWORD=
TTS_BASE_URL=https://api-smartflo.tatateleservices.com
GEMINI_API_KEY=
FRONTEND_ORIGINS=https://your-app.vercel.app,https://your-preview.vercel.app
ENVIRONMENT=development

### frontend/.env
VITE_API_BASE_URL=http://localhost:8000

## Future Improvements (v2)
### Dashboard latency (current bottleneck: TTS CDR API round-trip on every Search)
1. **Backend CDR cache** — Cache CDR results in memory (e.g. functools.lru_cache or Redis) keyed by (from_date, to_date). TTL ~5 min. Eliminates repeated TTS calls for same range.
2. **Single CDR fetch for both endpoints** — Today `/overall` and `/agent` each independently call TTS. A shared cache means the second query is instant.
3. **Stale-while-revalidate on frontend** — Set `staleTime: 5 * 60 * 1000` on both TanStack queries so navigating back to Dashboard shows cached data immediately while refreshing in background.
4. **Pagination cap** — Limit CDR pages fetched to a configurable MAX_PAGES (e.g. 10) and surface a warning if the range is too wide. Prevents unbounded API calls for large date ranges.
5. **Date range presets** — Add "Today / Last 7 days / This month" quick-select buttons so users don't need to type dates.
