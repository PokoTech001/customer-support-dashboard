from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------


class HourlyBucket(BaseModel):
    hour: int        # 0–23
    answered: int
    missed: int


class DailyBucket(BaseModel):
    date: str        # "YYYY-MM-DD"
    answered: int
    missed: int


# ---------------------------------------------------------------------------
# /api/calls/overall
# ---------------------------------------------------------------------------


class OverallAnalyticsResponse(BaseModel):
    total_inbound: int
    answered: int
    missed: int
    answer_rate: float          # 0–100 %
    avg_handle_time: float      # seconds (call_duration)
    avg_talk_time: float        # seconds (answered_seconds / talk time only)
    sla_compliance: float       # 0–100 %
    hourly_distribution: list[HourlyBucket]   # always 24 entries, hours 0–23
    daily_distribution: list[DailyBucket]     # one entry per calendar date in range


# ---------------------------------------------------------------------------
# /api/calls/agent
# ---------------------------------------------------------------------------


class AgentMetrics(BaseModel):
    agent_name: str
    answered: int
    missed: int
    answer_rate: float          # 0–100 %
    avg_talk_time: float        # seconds
    first_call_resolution: float  # 0–100 %
    sla_compliance: float       # 0–100 %


class AgentAnalyticsResponse(BaseModel):
    agents: list[AgentMetrics]


# ---------------------------------------------------------------------------
# /api/agents/list
# ---------------------------------------------------------------------------


class AgentListItem(BaseModel):
    id: str
    name: str
    extension: str | None = None


class AgentListResponse(BaseModel):
    agents: list[AgentListItem]


# ---------------------------------------------------------------------------
# /api/recordings/search
# ---------------------------------------------------------------------------


class RecordingSearchResult(BaseModel):
    call_id: str
    agent_name: str
    date: str
    time: str
    duration: int               # seconds
    # recording_url is intentionally omitted — audio is served via
    # GET /api/recordings/{call_id}/audio so TTS URLs never reach the frontend


class RecordingSearchResponse(BaseModel):
    results: list[RecordingSearchResult]


# ---------------------------------------------------------------------------
# /api/analyze — TranscriptAnalysisResult
# ---------------------------------------------------------------------------


class TranscriptTurn(BaseModel):
    speaker: str      # real agent name | "Customer" | "Unknown"
    timestamp: str    # "MM:SS" — used by frontend to sync with audio currentTime
    text: str


class TranscribeResponse(BaseModel):
    language_detected: list[str]
    transcript: list[TranscriptTurn]


class TranscriptAnalysisResult(BaseModel):
    call_id: str | None = None
    language_detected: list[str]
    transcript: list[TranscriptTurn]
    query_buckets: list[str]
    sentiment: str              # "Positive" | "Neutral" | "Negative"
    sentiment_score: float      # 0.0–1.0
    agent_tone: str
    agent_performance_score: float   # 0.0–10.0
    performance_reasoning: str
    recommendations: list[str]
    call_summary: str


# ---------------------------------------------------------------------------
# /api/analyze — request bodies
# ---------------------------------------------------------------------------


class CallAnalysisRequest(BaseModel):
    call_id: str
    agent_name: str = "Agent"   # frontend passes the real name from search results
