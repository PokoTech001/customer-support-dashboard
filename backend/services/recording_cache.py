"""
Shared short-lived cache: call_id → (recording_url, mime).

Populated by /api/recordings/search; consumed by both
/api/recordings/{call_id}/audio and /api/analyze/transcribe|from-recording.
TTL is 10 minutes — long enough for a user to search then press play/analyze.
"""

import time
from dataclasses import dataclass

_TTL = 600  # 10 minutes


@dataclass
class CacheEntry:
    recording_url: str
    mime: str
    expires_at: float


_store: dict[str, CacheEntry] = {}

_MIME_MAP = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
}


def mime_for_url(url: str) -> str:
    lower = url.lower()
    for ext, mime in _MIME_MAP.items():
        if ext in lower:
            return mime
    return "audio/mpeg"


def put(call_id: str, recording_url: str) -> None:
    _store[call_id] = CacheEntry(
        recording_url=recording_url,
        mime=mime_for_url(recording_url),
        expires_at=time.monotonic() + _TTL,
    )


def get(call_id: str) -> CacheEntry | None:
    entry = _store.get(call_id)
    if entry is None:
        return None
    if time.monotonic() > entry.expires_at:
        del _store[call_id]
        return None
    return entry
