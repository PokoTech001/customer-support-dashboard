# Customer Support Dashboard & Transcript Analytics — Technical Spec
**Version:** 1.0 | **Date:** June 2026  
**Stack:** FastAPI (Python) + React (TypeScript) | **Deploy:** Render + Vercel

---

## 1. Project Overview

A two-page internal web app for customer support personnel training:

| Page | Purpose |
|---|---|
| **Dashboard** | Call analytics — overall + agent-wise, sourced from SmartFlo API |
| **Transcript Analytics** | AI-powered call analysis — transcription, diarization, sentiment, coaching |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (React + TypeScript)                              │
│  Vercel / Netlify                                           │
│  ├── /dashboard  → Dashboard Page                          │
│  └── /transcripts → Transcript Analytics Page              │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS REST
┌────────────────────▼────────────────────────────────────────┐
│  BACKEND (FastAPI, Python 3.11+)                            │
│  Render (Web Service)                                       │
│  ├── /api/auth        → TTS token management               │
│  ├── /api/calls       → CDR + analytics aggregation        │
│  ├── /api/agents      → Agent list + per-agent metrics     │
│  ├── /api/recordings  → Fetch recording URLs from TTS      │
│  └── /api/analyze     → Gemini analysis pipeline           │
└───────┬────────────────────────────┬────────────────────────┘
        │                            │
        ▼                            ▼
 SmartFlo API                  Google Gemini 2.0 Flash API
 api-smartflo.tatateleservices.com   generativelanguage.googleapis.com
```

---

## 3. External APIs

### 3.1 SmartFlo (TTS) API

**Base URL:** `https://api-smartflo.tatateleservices.com`  
**Auth:** Bearer token (JWT), obtained via login, valid 3600s → auto-refresh via `/v1/auth/refresh`

#### Endpoints We Use

| Purpose | Method | Endpoint |
|---|---|---|
| Login / get token | POST | `/v1/auth/login` |
| Refresh token | POST | `/v1/auth/refresh` |
| Logout | DELETE | `/v1/auth/logout` |
| **Call Detail Records (CDR)** | GET | `/v1/call/records` |
| Fetch agents/users | GET | `/v1/users` (fetch-multiple-users) |
| Live/active calls | GET | `/v1/live_calls` |

#### CDR Key Query Params
```
from_date     : "Y-m-d H:i:s"
to_date       : "Y-m-d H:i:s"
direction     : "inbound" | "outbound"
call_type     : "c" (answered) | "m" (missed)
agents        : array of "agent|<id>"
page          : int
limit         : int (max ~100 recommended)
call_id       : string (for single call lookup)
```

#### CDR Key Response Fields We Use
```
results[].status           → "answered" | "missed"
results[].direction        → "inbound" | "outbound"
results[].agent_name       → string
results[].date             → "YYYY-MM-DD"
results[].time             → "HH:MM:SS"
results[].call_duration    → int (seconds, total)
results[].answered_seconds → int (talk time)
results[].recording_url    → string (downloadable mp3)
results[].call_id          → string (unique)
results[].dialer_call_details.sla_status
results[].dialer_call_details.first_call_resolution
results[].dialer_call_details.disposition_name
results[].missed_agents[]
```

**Rate Limit:** TTS imposes rate limits — backend must implement token bucket / retry logic.  
**Pagination:** Page through all results using `page` param; stop when `results` is empty.

---

### 3.2 Google Gemini 2.0 Flash API

**Model:** `gemini-2.0-flash`  
**Used for:** Audio transcription + diarization + analysis in a single multimodal call  
**Auth:** API Key via `x-goog-api-key` header  
**Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`

#### Audio Input
- Inline base64 for files < ~10MB
- File API (upload first) for larger files
- Supported format: `audio/mpeg` (mp3), `audio/wav`, `audio/ogg`

#### What We Ask Gemini to Do (Single Prompt)
1. Diarize the conversation (Speaker 1 = Agent, Speaker 2 = Customer)
2. Transcribe with timestamps — output in clean conversational format
3. Detect language(s) spoken
4. Extract query buckets / issue categories
5. Assess overall call sentiment (Positive / Neutral / Negative)
6. Evaluate agent tone (Empathetic / Neutral / Curt / etc.)
7. Score agent performance (0–10) with reasoning
8. Generate 3–5 specific coaching recommendations

**Languages supported:** Hindi, Kannada, Telugu, Tamil, Malayalam, Marathi, English (and Hinglish/code-switching variants)

---

## 4. Backend — FastAPI

### 4.1 Project Structure
```
backend/
├── main.py
├── requirements.txt
├── .env.example
├── config.py                  # Settings via pydantic-settings
├── routers/
│   ├── calls.py               # /api/calls/*
│   ├── agents.py              # /api/agents/*
│   ├── recordings.py          # /api/recordings/*
│   └── analyze.py             # /api/analyze/*
├── services/
│   ├── tts_client.py          # SmartFlo API client (auth + CDR)
│   ├── gemini_client.py       # Gemini API client
│   └── aggregator.py          # Analytics computation logic
├── models/
│   ├── schemas.py             # Pydantic request/response models
│   └── enums.py
└── utils/
    ├── auth.py                # Token cache + refresh logic
    └── pagination.py          # TTS pagination helpers
```

### 4.2 Key Endpoints (Our FastAPI)

#### Calls / Analytics
```
GET  /api/calls/overall
     Query: from_date, to_date
     Returns: total_inbound, answered, missed, hourly_distribution[24],
              daily_distribution[31], avg_handle_time, answer_rate

GET  /api/calls/agent
     Query: from_date, to_date, agent_id (optional)
     Returns: per-agent breakdown of answered, missed, avg_duration,
              first_call_resolution, sla_compliance
```

#### Agents
```
GET  /api/agents/list
     Returns: [{id, name, extension}] — sourced from TTS users API
```

#### Recordings (for Transcript page)
```
GET  /api/recordings/search
     Query: from_date, to_date, agent_name, call_id
     Returns: [{call_id, agent_name, date, time, duration, recording_url}]
```

#### Analysis
```
POST /api/analyze/upload
     Body: multipart/form-data { file: mp3 }
     Returns: TranscriptAnalysisResult

POST /api/analyze/from-recording
     Body: { call_id: string } OR { recording_url: string }
     Returns: TranscriptAnalysisResult
```

#### TranscriptAnalysisResult schema
```json
{
  "call_id": "string",
  "language_detected": ["Hindi", "English"],
  "transcript": [
    {"speaker": "Agent", "timestamp": "0:00:03", "text": "Namaste, main aapki kaise madad kar sakta hoon?"},
    {"speaker": "Customer", "timestamp": "0:00:07", "text": "Mera order abhi tak nahi aaya."}
  ],
  "query_buckets": ["Order Delay", "Delivery Status"],
  "sentiment": "Negative",
  "sentiment_score": 0.3,
  "agent_tone": "Empathetic",
  "agent_performance_score": 7.5,
  "performance_reasoning": "Agent acknowledged the issue promptly...",
  "recommendations": [
    "Proactively offer compensation for delays",
    "Use more reassuring language in closing"
  ],
  "call_summary": "Customer called regarding a delayed order. Agent checked status and promised resolution within 24 hours."
}
```

### 4.3 Token Management (TTS)
- On startup: authenticate with stored credentials → cache bearer token
- Store expiry timestamp; refresh 5 minutes before expiry
- All TTS API calls go through `tts_client.py` which handles this transparently
- Credentials stored in `.env`, never hardcoded

### 4.4 Environment Variables
```env
# TTS SmartFlo
TTS_EMAIL=your@email.com
TTS_PASSWORD=yourpassword
TTS_BASE_URL=https://api-smartflo.tatateleservices.com

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key

# App
FRONTEND_ORIGIN=https://your-frontend.vercel.app
ENVIRONMENT=production
```

### 4.5 CORS
Allow only `FRONTEND_ORIGIN` in production. Allow `*` in dev.

### 4.6 Deployment — Render
- **Service type:** Web Service
- **Runtime:** Python 3.11
- **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Build command:** `pip install -r requirements.txt`
- **Env vars:** Set in Render dashboard (never in code)
- **Health check:** `GET /health` → `{"status": "ok"}`

---

## 5. Frontend — React + TypeScript

### 5.1 Tech Stack
```
React 18 + TypeScript
Vite (build tool)
React Router v6 (routing)
TanStack Query (data fetching + caching)
Recharts (charts)
shadcn/ui + Tailwind CSS (UI components)
Axios (HTTP client)
date-fns (date manipulation)
react-dropzone (file upload)
```

### 5.2 Project Structure
```
frontend/
├── src/
│   ├── pages/
│   │   ├── DashboardPage.tsx
│   │   └── TranscriptPage.tsx
│   ├── components/
│   │   ├── dashboard/
│   │   │   ├── OverallAnalytics.tsx
│   │   │   ├── AgentAnalytics.tsx
│   │   │   ├── HourlyDistributionChart.tsx
│   │   │   ├── DailyDistributionChart.tsx
│   │   │   ├── KPICard.tsx
│   │   │   └── DateRangePicker.tsx
│   │   ├── transcript/
│   │   │   ├── FileUploadZone.tsx
│   │   │   ├── RecordingSearchFilter.tsx
│   │   │   ├── RecordingResultsTable.tsx
│   │   │   ├── TranscriptViewer.tsx
│   │   │   ├── AnalysisPanel.tsx
│   │   │   └── ScoreCard.tsx
│   │   └── shared/
│   │       ├── Navbar.tsx
│   │       ├── LoadingSpinner.tsx
│   │       └── ErrorBoundary.tsx
│   ├── hooks/
│   │   ├── useOverallAnalytics.ts
│   │   ├── useAgentAnalytics.ts
│   │   └── useAnalysis.ts
│   ├── api/
│   │   ├── calls.ts
│   │   ├── agents.ts
│   │   ├── recordings.ts
│   │   └── analyze.ts
│   ├── types/
│   │   └── index.ts
│   └── utils/
│       └── formatters.ts
├── .env.example
└── vite.config.ts
```

### 5.3 Page 1 — Dashboard

#### Section A: Overall Analytics
**Filters:** Date range picker (default: last 7 days)

**KPI Cards (top row):**
- Total Inbound Calls
- Calls Answered (+ % answer rate)
- Calls Missed (+ % miss rate)
- Avg Handle Time
- Avg Talk Time
- SLA Compliance %

**Charts:**
- Hourly Call Distribution (Bar chart, 24h, answered vs missed stacked)
- Day-wise Distribution (Bar chart, current month)

#### Section B: Agent-wise Analytics
**Filters:** Agent dropdown (multi-select), Date range picker

**Table columns:**
- Agent Name
- Calls Attended
- Calls Missed
- Answer Rate %
- Avg Talk Time
- First Call Resolution %
- SLA Compliance %

Clicking an agent row expands a mini-chart of their daily call volume.

### 5.4 Page 2 — Transcript Analytics

**Two input modes (tabbed):**

**Tab 1: Upload MP3**
- Drag-and-drop zone, max 50MB
- Shows file name + duration after upload
- "Analyze" button triggers `POST /api/analyze/upload`

**Tab 2: Import from SmartFlo**
- Filters: Date, Time range, Agent Name (text search), Call ID
- "Search" → shows table of matching recordings
- Each row has: Date, Time, Agent, Duration, [Analyze] button
- Clicking Analyze triggers `POST /api/analyze/from-recording`

**Analysis Output (shown after processing):**

1. **Language Badge** — detected language(s)
2. **Transcript Viewer** — clean conversation UI
   - Agent turns: left-aligned, blue accent
   - Customer turns: right-aligned, gray
   - Timestamp shown per turn
3. **Query Buckets** — tag chips (e.g. "Order Delay", "Refund Request")
4. **Sentiment Gauge** — Positive / Neutral / Negative with color
5. **Agent Tone** — labeled badge (Empathetic / Curt / etc.)
6. **Performance Score** — circular score (0–10) with reasoning text
7. **Recommendations** — numbered list, each as a distinct card
8. **Call Summary** — one-paragraph summary

Processing state: Show animated loading with step labels ("Downloading recording...", "Analyzing with AI...", "Generating insights...")

### 5.5 Frontend Environment Variables
```env
VITE_API_BASE_URL=https://your-backend.onrender.com
```

### 5.6 Deployment — Vercel
- Connect GitHub repo, set root to `/frontend`
- Framework preset: Vite
- Set `VITE_API_BASE_URL` in Vercel env settings

---

## 6. Data Flow Diagrams

### Dashboard Load
```
User sets date filter
  → Frontend calls GET /api/calls/overall?from_date=...&to_date=...
  → Backend: check TTS token validity → refresh if needed
  → Backend: paginate through GET /v1/call/records (TTS) for date range
  → Backend: aggregate in aggregator.py (hourly buckets, totals, per-agent)
  → Return aggregated JSON to frontend
  → Recharts renders charts
```

### Transcript Analysis (Upload)
```
User uploads MP3
  → Frontend: POST /api/analyze/upload (multipart)
  → Backend: receive file, encode base64
  → Backend: call Gemini 2.0 Flash with audio + structured prompt
  → Gemini: returns transcript + all analysis fields
  → Backend: parse + validate → return TranscriptAnalysisResult
  → Frontend: render transcript viewer + analysis panels
```

### Transcript Analysis (From SmartFlo)
```
User searches recordings
  → GET /api/recordings/search → TTS CDR API
  → User clicks Analyze on a recording
  → Backend: download audio from recording_url (TTS signed URL)
  → Same Gemini pipeline as upload
```

---

## 7. Gemini Prompt Design

```python
ANALYSIS_PROMPT = """
You are an expert call center quality analyst for an Indian customer support operation.

Analyze this call recording between a customer support agent and a customer.
The call may be in Hindi, Kannada, Telugu, Tamil, Malayalam, Marathi, English,
or a mix (code-switching is common).

Respond ONLY in the following JSON structure — no markdown, no explanation outside JSON:

{
  "language_detected": ["<lang1>", "<lang2>"],
  "transcript": [
    {"speaker": "Agent", "timestamp": "H:MM:SS", "text": "<original language text>"},
    {"speaker": "Customer", "timestamp": "H:MM:SS", "text": "<original language text>"}
  ],
  "query_buckets": ["<issue category 1>", ...],
  "sentiment": "Positive|Neutral|Negative",
  "sentiment_score": <0.0 to 1.0>,
  "agent_tone": "Empathetic|Professional|Curt|Confused|Reassuring|Dismissive",
  "agent_performance_score": <0.0 to 10.0>,
  "performance_reasoning": "<2-3 sentence explanation>",
  "recommendations": ["<specific actionable tip 1>", "<tip 2>", ...],
  "call_summary": "<1 paragraph summary in English>"
}

Rules:
- Keep transcript text in the ORIGINAL language spoken (do not translate)
- If you cannot determine speaker from audio context, label as "Unknown"
- Query buckets should be concise 2-4 word categories relevant to customer support
- Recommendations must be specific and actionable for agent training
"""
```

---

## 8. Key Technical Decisions & Rationale

| Decision | Choice | Reason |
|---|---|---|
| Transcription model | Gemini 2.0 Flash | Native audio input, handles all 6 Indian languages + code-switching, single API call for transcript + analysis |
| Backend framework | FastAPI | Async support (critical for Gemini + TTS calls), Python ecosystem for data processing |
| Frontend state | TanStack Query | Built-in caching, background refetch, loading/error states — avoids manual fetch boilerplate |
| Charts | Recharts | React-native, well-maintained, good for bar/line needed here |
| Deployment | Render + Vercel | Free tiers sufficient for MVP; Render handles long-running analysis requests |
| Auth to TTS | Backend-only | Never expose TTS credentials to frontend; all TTS calls proxied through our backend |

---

## 9. Known Constraints & Mitigations

| Constraint | Mitigation |
|---|---|
| TTS token expires in 3600s | Auto-refresh 5 min before expiry; store in-memory with lock |
| Recording URLs may be short-lived | Download immediately after fetching CDR; don't cache URLs |
| Gemini file size limit ~20MB inline | Stream large files via Gemini File API; add client-side size warning |
| TTS rate limits on CDR API | Implement exponential backoff + request queue in `tts_client.py` |
| Analysis latency (10-30s for long calls) | SSE (Server-Sent Events) or polling endpoint for progress updates |
| Gemini hallucination on poor audio | Add confidence threshold; flag low-quality transcripts with warning UI |

---

## 10. Implementation Phases

### Phase 1 — Backend Foundation (Week 1)
- [ ] FastAPI project scaffold
- [ ] TTS auth + CDR client with token management
- [ ] `/api/calls/overall` and `/api/calls/agent` endpoints
- [ ] `/api/agents/list` endpoint
- [ ] Unit tests for aggregator logic

### Phase 2 — Frontend Dashboard (Week 1-2)
- [ ] React + Vite + Tailwind setup
- [ ] Dashboard page with KPI cards
- [ ] Hourly + daily charts
- [ ] Agent table with filters

### Phase 3 — Transcript Backend (Week 2)
- [ ] Gemini client with audio ingestion
- [ ] `/api/analyze/upload` endpoint
- [ ] `/api/analyze/from-recording` endpoint
- [ ] `/api/recordings/search` endpoint
- [ ] Prompt tuning with sample calls

### Phase 4 — Transcript Frontend (Week 2-3)
- [ ] File upload zone
- [ ] Recording search + table
- [ ] Transcript viewer component
- [ ] Analysis panels (sentiment, score, recommendations)

### Phase 5 — Polish + Deploy (Week 3)
- [ ] Error handling everywhere
- [ ] Loading states + progress indicators
- [ ] Deploy backend to Render
- [ ] Deploy frontend to Vercel
- [ ] End-to-end testing with real calls

---

## 11. Security Notes
- TTS credentials: backend `.env` only, Render environment secrets in prod
- Gemini key: same
- No credentials in frontend code ever
- CORS restricted to frontend domain in production
- Recording audio is not stored server-side — processed in-memory and discarded
- No PII (customer phone numbers) logged

---

## 12. Estimated Costs (Monthly, MVP Scale)

| Service | Estimate |
|---|---|
| Render (Web Service, free tier) | $0 (spins down after 15min inactivity — upgrade to $7/mo for always-on) |
| Vercel (Hobby) | $0 |
| Gemini 2.0 Flash (per analysis) | ~$0.01–0.05 per call (audio input is ~$0.001/min + output tokens) |
| TTS SmartFlo | Already paying for telephony service |

---

*End of Technical Spec v1.0*
