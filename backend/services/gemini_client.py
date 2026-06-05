"""
Google Gemini 2.0 Flash client.

Two public methods:
  transcribe(audio, mime, agent_name) → TranscribeResult
  analyze(audio, mime, agent_name)    → AnalysisResult

Both return plain dicts; the routers coerce them into Pydantic models.
Audio < 20 MB is sent inline (base64). Larger files use the Gemini File API.
"""

import base64
import json
import logging
import re

import httpx

from config import settings

logger = logging.getLogger(__name__)

_GENERATE_URL = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/models/gemini-2.5-flash-lite:generateContent"
)
_UPLOAD_URL = (
    "https://generativelanguage.googleapis.com/upload/v1beta/files"
)
_INLINE_LIMIT = 20 * 1024 * 1024  # 20 MB


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


def _transcribe_prompt(agent_name: str) -> str:
    return f"""You are transcribing a customer support call recording.
The support agent's name is {agent_name}. The other speaker is the customer.
Label agent turns as "{agent_name}" and customer turns as "Customer".
The call may be in Hindi, Kannada, Telugu, Tamil, Malayalam, Marathi, English, or mixed.
Keep transcript text in the ORIGINAL language spoken — do not translate.
Use MM:SS format for all timestamps (e.g. 00:03, 01:23, 12:05).

Respond ONLY in this exact JSON structure — no markdown, no text outside the JSON:

{{
  "language_detected": ["<lang1>", "<lang2>"],
  "transcript": [
    {{"speaker": "{agent_name}", "timestamp": "MM:SS", "text": "<original text>"}},
    {{"speaker": "Customer",     "timestamp": "MM:SS", "text": "<original text>"}}
  ]
}}"""


def _analysis_prompt(agent_name: str) -> str:
    return f"""You are an expert call centre quality analyst for an Indian customer support operation.
The support agent's name is {agent_name}. The other speaker is the customer.
Label agent turns as "{agent_name}" and customer turns as "Customer".
The call may be in Hindi, Kannada, Telugu, Tamil, Malayalam, Marathi, English, or mixed (code-switching is common).
Keep transcript text in the ORIGINAL language spoken — do not translate.
Use MM:SS format for all timestamps (e.g. 00:03, 01:23).

Respond ONLY in this exact JSON structure — no markdown, no text outside the JSON:

{{
  "language_detected": ["<lang1>", "<lang2>"],
  "transcript": [
    {{"speaker": "{agent_name}", "timestamp": "MM:SS", "text": "<original text>"}},
    {{"speaker": "Customer",     "timestamp": "MM:SS", "text": "<original text>"}}
  ],
  "query_buckets": ["<2-4 word issue category>"],
  "sentiment": "Positive|Neutral|Negative",
  "sentiment_score": 0.0,
  "agent_tone": "Empathetic|Professional|Curt|Confused|Reassuring|Dismissive",
  "agent_performance_score": 0.0,
  "performance_reasoning": "<2-3 sentence explanation>",
  "recommendations": ["<specific actionable tip>"],
  "call_summary": "<one paragraph summary in English>"
}}

Rules:
- query_buckets: concise 2-4 word categories (e.g. "Order Delay", "Refund Request")
- recommendations: specific and actionable for agent training
- call_summary: always in English regardless of call language
- If speaker cannot be determined from audio, use "Unknown\""""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _auth_header() -> dict[str, str]:
    return {"x-goog-api-key": settings.gemini_api_key}


def _normalize_timestamp(raw: str) -> str:
    """Convert any timestamp variant (H:MM:SS, M:SS, SS) → MM:SS."""
    try:
        parts = str(raw).strip().split(":")
        if len(parts) == 1:
            total = int(float(parts[0]))
        elif len(parts) == 2:
            total = int(parts[0]) * 60 + int(parts[1])
        else:
            total = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        mm, ss = divmod(total, 60)
        return f"{mm:02d}:{ss:02d}"
    except (ValueError, IndexError):
        return "00:00"


def _extract_json(text: str) -> dict:
    """Strip any markdown fencing Gemini may wrap around the JSON."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


def _normalise_transcript(data: dict) -> dict:
    """Ensure all transcript timestamps are in MM:SS format."""
    for turn in data.get("transcript", []):
        turn["timestamp"] = _normalize_timestamp(turn.get("timestamp", "0"))
    return data


async def _upload_to_file_api(
    client: httpx.AsyncClient, audio: bytes, mime: str
) -> str:
    """Upload audio via Gemini File API and return the file URI."""
    boundary = "upload_boundary_x7k2"
    metadata = json.dumps({"file": {"display_name": "recording"}}).encode()

    body = b"".join([
        f"--{boundary}\r\nContent-Type: application/json; charset=utf-8\r\n\r\n".encode(),
        metadata,
        f"\r\n--{boundary}\r\nContent-Type: {mime}\r\n\r\n".encode(),
        audio,
        f"\r\n--{boundary}--".encode(),
    ])

    resp = await client.post(
        _UPLOAD_URL,
        headers={
            **_auth_header(),
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
        content=body,
        timeout=120.0,
    )
    resp.raise_for_status()
    return resp.json()["file"]["uri"]


async def _call_gemini(
    client: httpx.AsyncClient,
    audio: bytes,
    mime: str,
    prompt: str,
) -> dict:
    if len(audio) >= _INLINE_LIMIT:
        file_uri = await _upload_to_file_api(client, audio, mime)
        audio_part: dict = {"file_data": {"mime_type": mime, "file_uri": file_uri}}
    else:
        audio_part = {
            "inline_data": {
                "mime_type": mime,
                "data": base64.b64encode(audio).decode(),
            }
        }

    payload = {
        "contents": [{"parts": [audio_part, {"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json",
        },
    }

    resp = await client.post(
        _GENERATE_URL,
        headers={**_auth_header(), "Content-Type": "application/json"},
        json=payload,
        timeout=180.0,
    )
    resp.raise_for_status()

    raw_text: str = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    data = _extract_json(raw_text)
    return _normalise_transcript(data)


# ---------------------------------------------------------------------------
# Public client
# ---------------------------------------------------------------------------


class GeminiClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient()

    async def close(self) -> None:
        await self._client.aclose()

    async def transcribe(
        self, audio: bytes, mime: str, agent_name: str
    ) -> dict:
        """Transcribe + diarise only. Returns {language_detected, transcript}."""
        logger.info("Gemini transcribe: %.1f KB, agent=%s", len(audio) / 1024, agent_name)
        return await _call_gemini(
            self._client, audio, mime, _transcribe_prompt(agent_name)
        )

    async def analyze(
        self, audio: bytes, mime: str, agent_name: str
    ) -> dict:
        """Full analysis. Returns complete TranscriptAnalysisResult dict."""
        logger.info("Gemini analyze: %.1f KB, agent=%s", len(audio) / 1024, agent_name)
        return await _call_gemini(
            self._client, audio, mime, _analysis_prompt(agent_name)
        )


gemini_client = GeminiClient()
