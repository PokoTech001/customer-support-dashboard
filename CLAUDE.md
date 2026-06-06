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
Phase 2 complete — Full app live on Render + Vercel. Both pages verified working in production.

## Deployment Status
| Service  | Platform | Status |
|----------|----------|--------|
| Backend  | Render   | Live — FastAPI docs confirmed working |
| Frontend | Vercel   | Live — Dashboard and Transcript pages confirmed working |

**Safe revert point:** commit `f9d3b55`
To revert: `git revert f9d3b55` or `git reset --hard f9d3b55`

### What was built (completed)
- [x] TTS client — auth, auto-refresh, CDR pagination, exponential backoff
- [x] Aggregator — overall KPIs, hourly/daily charts, per-agent metrics
- [x] `/api/calls/overall` and `/api/calls/agent` endpoints
- [x] Recording cache — short-lived server-side store, TTL 10 min
- [x] `/api/recordings/search` — search CDRs, populate cache
- [x] `/api/recordings/{call_id}/audio` — stream audio, Range request support
- [x] Gemini client — transcribe-only + full analysis, inline/File API, timestamp normalisation
- [x] `/api/analyze/transcribe`, `/api/analyze/from-recording`, `/api/analyze/upload`
- [x] React frontend — Dashboard page (KPIs, hourly/daily charts, agent table)
- [x] React frontend — Transcript page (recordings table, Spotify-style curtain, audio sync)
- [x] CORS fix — `FRONTEND_ORIGINS` comma-separated, `["*"]` in dev
- [x] Local deployment verified working end-to-end
- [x] Render + Vercel production deployment verified working

### What to do next (v2)
- [ ] Test `/api/analyze/transcribe` and `/api/analyze/from-recording` in production with valid Gemini API key
- [ ] Add date range quick-select presets (Today / Last 7 days / This month) to Dashboard
- [ ] Reduce dashboard latency — see Future Improvements section below
- [ ] Add agent filter dropdown to Transcript search (currently free-text only)
- [ ] Add `/api/agents/list` endpoint (router stub exists in schemas.py)
- [ ] Error boundary on frontend — graceful fallback if backend goes cold on Render (free tier spins down)

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
