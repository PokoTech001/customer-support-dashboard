# How to Set Up Claude Context in VS Code for This Project

This guide tells you exactly how to give Claude (in VS Code via Claude Code) the right context so it codes accurately without you re-explaining the project every session.

---

## Step 1 — Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Then open VS Code in your project root and run:
```bash
claude
```

---

## Step 2 — Project Folder Structure to Create First

Before writing any code, create this layout:

```
support-dashboard/
├── CLAUDE.md                  ← PRIMARY context file (Claude reads this automatically)
├── docs/
│   ├── TECHNICAL_SPEC.md      ← The spec file you already have
│   ├── tts_api_reference.md   ← TTS API docs (instructions below)
│   └── gemini_api_notes.md    ← Gemini notes (instructions below)
├── backend/
│   └── (FastAPI code goes here)
└── frontend/
    └── (React code goes here)
```

---

## Step 3 — Create CLAUDE.md (Most Important File)

Create a file named exactly `CLAUDE.md` in your project root. Claude Code reads this automatically at the start of every session. Paste this content and fill in your specifics:

```markdown
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
[UPDATE THIS as you progress]
Phase 1 — Building backend TTS client and CDR aggregation

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
FRONTEND_ORIGIN=https://your-app.vercel.app
ENVIRONMENT=development

### frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```

---

## Step 4 — Create the TTS API Reference Doc

Create `docs/tts_api_reference.md`. You have two options:

### Option A — Automated (recommended)
Run this in your terminal to download the key API pages:

```bash
# Install if needed
pip install requests markdownify

# Run this Python script
python3 - <<'EOF'
import requests

urls = [
    "https://docs.smartflo.tatatelebusiness.com/reference/generate-a-token.md",
    "https://docs.smartflo.tatatelebusiness.com/reference/v1callrecords.md",
    "https://docs.smartflo.tatatelebusiness.com/reference/v1authrefresh.md",
    "https://docs.smartflo.tatatelebusiness.com/reference/v1live_calls.md",
    "https://docs.smartflo.tatatelebusiness.com/reference/fetch-multiple-users.md",
]

combined = "# SmartFlo API Reference — Relevant Endpoints\n\n"
for url in urls:
    r = requests.get(url)
    combined += f"\n\n---\n\n{r.text}"

with open("docs/tts_api_reference.md", "w") as f:
    f.write(combined)

print("Done — docs/tts_api_reference.md created")
EOF
```

### Option B — Manual
Copy the content of these pages using the MarkDownload browser extension and paste into `docs/tts_api_reference.md`:
- https://docs.smartflo.tatatelebusiness.com/reference/generate-a-token.md
- https://docs.smartflo.tatatelebusiness.com/reference/v1callrecords.md
- https://docs.smartflo.tatatelebusiness.com/reference/v1authrefresh.md

---

## Step 5 — Create Gemini API Notes

Create `docs/gemini_api_notes.md` with this content (already researched):

```markdown
# Gemini 2.0 Flash — Audio Analysis Notes

## Model
gemini-2.0-flash

## Endpoint
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
Header: x-goog-api-key: YOUR_KEY

## Audio Input Pattern (Python)
import google.generativeai as genai
import base64

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

# For files < ~10MB: inline base64
with open("call.mp3", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode()

response = model.generate_content([
    {"inline_data": {"mime_type": "audio/mpeg", "data": audio_data}},
    ANALYSIS_PROMPT
])

# For files > 10MB: use File API
import google.generativeai as genai
audio_file = genai.upload_file("call.mp3", mime_type="audio/mpeg")
response = model.generate_content([audio_file, ANALYSIS_PROMPT])

## Supported Languages (confirmed)
Hindi, Kannada, Telugu, Tamil, Malayalam, Marathi, English, Hinglish (code-switching)

## Pricing (approximate)
Audio input: ~$0.001 per minute
Output tokens: ~$0.0006 per 1K tokens
Typical call analysis (5 min call): ~$0.01–0.03 total

## Key Limitation
Max inline audio: ~20MB
Max via File API: 2GB
File API uploaded files expire after 48 hours
```

---

## Step 6 — How to Talk to Claude in VS Code

### Starting a session
```
claude
```

Claude will automatically read CLAUDE.md. You don't need to re-explain the project.

### Useful commands to give Claude
```
# Start a specific task
"Implement the TTS client in backend/services/tts_client.py following the spec in docs/TECHNICAL_SPEC.md"

# Reference a specific file
"Based on docs/tts_api_reference.md, implement the CDR aggregation endpoint in backend/routers/calls.py"

# Continue work
"Continue Phase 1 from CLAUDE.md — what's left to implement?"

# Ask Claude to check its own work
"Review backend/services/tts_client.py against the constraints in CLAUDE.md and fix any issues"
```

### Updating CLAUDE.md as you progress
After completing each phase, update the `## Current Phase` section in CLAUDE.md:
```markdown
## Current Phase
Phase 2 — Building React dashboard frontend
Completed: backend TTS client, CDR endpoints, agents endpoint
Next: Dashboard KPI cards, Recharts integration
```

---

## Step 7 — .gitignore

Make sure your `.gitignore` has:
```
backend/.env
frontend/.env
*.pyc
__pycache__/
node_modules/
.venv/
dist/
```

Never commit `.env` files. Use `.env.example` with empty values as a template.

---

## Summary: Files Claude Needs to Do Good Work

| File | Why |
|---|---|
| `CLAUDE.md` | Auto-loaded by Claude Code — project identity, stack, constraints, current phase |
| `docs/TECHNICAL_SPEC.md` | Full architecture, endpoint schemas, data models |
| `docs/tts_api_reference.md` | Exact SmartFlo API params and response shapes |
| `docs/gemini_api_notes.md` | Audio input pattern, model name, pricing |

With these 4 files in place, Claude Code has everything it needs to implement accurately without guessing.

---

## Common Mistakes to Avoid

1. **Don't skip CLAUDE.md** — without it, Claude loses project context between sessions
2. **Don't add credentials to CLAUDE.md** — it may be read by Claude; keep secrets only in .env
3. **Don't ask Claude to call TTS APIs from the frontend** — spec says backend-only
4. **Update CLAUDE.md's current phase** as you progress — stale phase info confuses Claude
5. **If Claude writes code that contradicts the spec** — point it to the specific section: *"See Section 4.3 in TECHNICAL_SPEC.md — token refresh must happen 5 minutes before expiry"*
