"""
/api/analyze — transcript and full analysis endpoints.

  POST /api/analyze/transcribe        → transcript only   (triggered by Play)
  POST /api/analyze/from-recording    → full analysis     (triggered by Analyze button)
  POST /api/analyze/upload            → full analysis     (triggered by file upload)

Transcribe and from-recording both require a prior /api/recordings/search call
within the last 10 minutes (recording_cache must be warm).
"""

import logging

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from models.schemas import (
    CallAnalysisRequest,
    TranscribeResponse,
    TranscriptAnalysisResult,
)
from services import recording_cache
from services.gemini_client import gemini_client
from services.tts_client import tts_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


def _cache_or_404(call_id: str):
    entry = recording_cache.get(call_id)
    if entry is None:
        raise HTTPException(
            404,
            detail=f"Recording for '{call_id}' not cached. Run a search first.",
        )
    return entry


async def _download_or_502(recording_url: str, call_id: str) -> bytes:
    try:
        return await tts_client.download_recording(recording_url)
    except httpx.HTTPStatusError as exc:
        logger.error("Audio download failed for %s: %s", call_id, exc.response.status_code)
        raise HTTPException(502, "Could not fetch audio from TTS") from exc


def _gemini_error(exc: Exception) -> HTTPException:
    logger.error("Gemini error: %s", exc)
    if isinstance(exc, httpx.HTTPStatusError):
        return HTTPException(502, f"Gemini API error: {exc.response.status_code}")
    return HTTPException(502, f"Gemini error: {exc}")


# ---------------------------------------------------------------------------
# Transcribe only — called when user presses Play
# ---------------------------------------------------------------------------


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_recording(req: CallAnalysisRequest) -> TranscribeResponse:
    """
    Diarise and transcribe the recording for call_id.
    Returns timestamped turns in MM:SS format — no quality analysis.
    Frontend uses timestamps to sync the transcript with audio playback.
    """
    entry = _cache_or_404(req.call_id)
    audio = await _download_or_502(entry.recording_url, req.call_id)

    try:
        result = await gemini_client.transcribe(audio, entry.mime, req.agent_name)
    except Exception as exc:
        raise _gemini_error(exc) from exc

    return TranscribeResponse(**result)


# ---------------------------------------------------------------------------
# Full analysis — called when user presses Analyze button
# ---------------------------------------------------------------------------


@router.post("/from-recording", response_model=TranscriptAnalysisResult)
async def analyze_from_recording(req: CallAnalysisRequest) -> TranscriptAnalysisResult:
    """
    Full quality analysis (transcript + sentiment + score + recommendations).
    Triggered only by explicit user action — never called automatically.
    """
    entry = _cache_or_404(req.call_id)
    audio = await _download_or_502(entry.recording_url, req.call_id)

    try:
        result = await gemini_client.analyze(audio, entry.mime, req.agent_name)
    except Exception as exc:
        raise _gemini_error(exc) from exc

    return TranscriptAnalysisResult(call_id=req.call_id, **result)


# ---------------------------------------------------------------------------
# Upload — full analysis on a user-supplied file
# ---------------------------------------------------------------------------


@router.post("/upload", response_model=TranscriptAnalysisResult)
async def analyze_upload(
    file: UploadFile = File(..., description="Audio file (mp3, wav, ogg, m4a)"),
    agent_name: str = Form(default="Agent", description="Agent name to label transcript turns"),
) -> TranscriptAnalysisResult:
    """
    Full quality analysis on an uploaded audio file.
    Accepts mp3, wav, ogg, m4a. Max ~20 MB inline; larger files use Gemini File API.
    """
    audio = await file.read()
    mime = file.content_type or recording_cache.mime_for_url(file.filename or "")

    try:
        result = await gemini_client.analyze(audio, mime, agent_name)
    except Exception as exc:
        raise _gemini_error(exc) from exc

    return TranscriptAnalysisResult(**result)
