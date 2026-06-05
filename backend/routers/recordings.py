"""
/api/recordings — search CDRs and stream audio.

TTS recording URLs are short-lived and must never be sent to the frontend.
recording_cache is populated by /search; /{call_id}/audio serves from it.
"""

import logging

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from models.schemas import RecordingSearchResponse, RecordingSearchResult
from services import recording_cache
from services.tts_client import tts_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recordings", tags=["recordings"])


def _range_response(audio: bytes, range_header: str, mime: str) -> Response:
    total = len(audio)
    raw = range_header.removeprefix("bytes=")
    start_s, _, end_s = raw.partition("-")
    start = int(start_s) if start_s.strip() else 0
    end = int(end_s) if end_s.strip() else total - 1
    end = min(end, total - 1)
    chunk = audio[start : end + 1]
    return Response(
        content=chunk,
        status_code=206,
        headers={
            "Content-Type": mime,
            "Content-Range": f"bytes {start}-{end}/{total}",
            "Content-Length": str(len(chunk)),
            "Accept-Ranges": "bytes",
        },
    )


@router.get("/search", response_model=RecordingSearchResponse)
async def search_recordings(
    from_date: str = Query(..., description='Format "YYYY-MM-DD HH:MM:SS"'),
    to_date: str = Query(..., description='Format "YYYY-MM-DD HH:MM:SS"'),
    agent_name: str | None = Query(None, description="Case-insensitive substring match"),
    call_id: str | None = Query(None, description="Exact call ID lookup"),
) -> RecordingSearchResponse:
    """
    Search CDRs and return metadata for calls that have a recording.
    Recording URLs are cached server-side; use /{call_id}/audio to stream.
    """
    try:
        cdrs = await tts_client.get_cdrs(
            from_date=from_date,
            to_date=to_date,
            call_id=call_id,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(502, f"TTS API error: {exc.response.status_code}") from exc

    results = []
    for cdr in cdrs:
        url: str = cdr.get("recording_url") or ""
        if not url:
            continue

        name = (cdr.get("agent_name") or "").strip()
        if agent_name and agent_name.lower() not in name.lower():
            continue

        cid: str = cdr.get("call_id") or ""
        if cid:
            recording_cache.put(cid, url)

        results.append(
            RecordingSearchResult(
                call_id=cid,
                agent_name=name or "Unknown",
                date=cdr.get("date") or "",
                time=cdr.get("time") or "",
                duration=int(cdr.get("call_duration") or 0),
            )
        )

    return RecordingSearchResponse(results=results)


@router.get("/{call_id}/audio")
async def stream_audio(call_id: str, request: Request) -> Response:
    """
    Stream recording audio. Supports Range requests for seeking.
    Requires a prior /search call within the last 10 minutes.
    """
    entry = recording_cache.get(call_id)
    if entry is None:
        raise HTTPException(
            404,
            detail=f"Recording for '{call_id}' not cached. Run a search first.",
        )

    try:
        audio = await tts_client.download_recording(entry.recording_url)
    except httpx.HTTPStatusError as exc:
        logger.error("Failed to download recording %s: %s", call_id, exc.response.status_code)
        raise HTTPException(502, "Could not fetch audio from TTS") from exc

    range_header = request.headers.get("range")
    if range_header:
        return _range_response(audio, range_header, entry.mime)

    return Response(
        content=audio,
        status_code=200,
        headers={
            "Content-Type": entry.mime,
            "Content-Length": str(len(audio)),
            "Accept-Ranges": "bytes",
            "Cache-Control": "private, max-age=60",
        },
    )
