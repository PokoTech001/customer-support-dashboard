"""
SmartFlo TTS API client.

Handles authentication (login / auto-refresh) and all CDR/user requests.
Token state is module-level so it's shared across all coroutines; refresh is
serialised via an asyncio.Lock to prevent concurrent re-logins.
"""

import asyncio
import logging
import time
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level token state
# ---------------------------------------------------------------------------

_token: str | None = None
_token_expires_at: float = 0.0  # Unix timestamp when the token expires
_refresh_lock = asyncio.Lock()

_REFRESH_BEFORE_SECS = 300  # refresh when less than 5 minutes remain
_MAX_RETRIES = 3
_BASE_BACKOFF_SECS = 1.0


# ---------------------------------------------------------------------------
# Auth helpers  (private)
# ---------------------------------------------------------------------------


def _is_token_valid() -> bool:
    return _token is not None and time.time() < _token_expires_at - _REFRESH_BEFORE_SECS


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token}"}


def _parse_token_response(data: dict[str, Any]) -> tuple[str, float]:
    """Extract (token_string, expires_at_unix) from a login/refresh response."""
    token = (
        data.get("token")
        or data.get("access_token")
        or (data.get("data") or {}).get("token")
    )
    if not token:
        raise ValueError(f"Could not extract token from TTS response: {list(data.keys())}")

    expires_in: int = int(data.get("expires_in") or data.get("expire_in") or 3600)
    return token, time.time() + expires_in


async def _do_login(client: httpx.AsyncClient) -> None:
    global _token, _token_expires_at

    resp = await client.post(
        f"{settings.tts_base_url}/v1/auth/login",
        json={"email": settings.tts_email, "password": settings.tts_password},
    )
    resp.raise_for_status()
    _token, _token_expires_at = _parse_token_response(resp.json())
    logger.info("TTS login successful; token valid for %.0fs", _token_expires_at - time.time())


async def _do_refresh(client: httpx.AsyncClient) -> None:
    """Attempt refresh; fall back to full login on failure."""
    global _token, _token_expires_at

    try:
        resp = await client.post(
            f"{settings.tts_base_url}/v1/auth/refresh",
            headers=_auth_headers(),
        )
        resp.raise_for_status()
        _token, _token_expires_at = _parse_token_response(resp.json())
        logger.info("TTS token refreshed; valid for %.0fs", _token_expires_at - time.time())
    except httpx.HTTPStatusError as exc:
        logger.warning("TTS token refresh failed (%s) — re-logging in", exc.response.status_code)
        await _do_login(client)


async def _ensure_token(client: httpx.AsyncClient) -> None:
    """Guarantee a valid token, serialising refresh to prevent stampedes."""
    if _is_token_valid():
        return
    async with _refresh_lock:
        if _is_token_valid():  # another coroutine may have refreshed already
            return
        if _token is not None:
            await _do_refresh(client)
        else:
            await _do_login(client)


# ---------------------------------------------------------------------------
# Retry-aware request helper  (private)
# ---------------------------------------------------------------------------


async def _request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs: Any,
) -> httpx.Response:
    """
    Authenticated request with exponential-backoff retry on 429 and a single
    token-refresh attempt on 401.
    """
    await _ensure_token(client)

    resp: httpx.Response | None = None
    for attempt in range(_MAX_RETRIES):
        headers = {**kwargs.pop("headers", {}), **_auth_headers()}
        resp = await client.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 429:
            wait = _BASE_BACKOFF_SECS * (2 ** attempt)
            logger.warning(
                "TTS rate-limited (429); retrying in %.1fs (attempt %d/%d)",
                wait,
                attempt + 1,
                _MAX_RETRIES,
            )
            await asyncio.sleep(wait)
            continue

        if resp.status_code == 401 and attempt == 0:
            logger.warning("TTS 401 — refreshing token and retrying")
            async with _refresh_lock:
                await _do_refresh(client)
            continue

        resp.raise_for_status()
        return resp

    # All retries exhausted — surface the last response as an error
    assert resp is not None
    resp.raise_for_status()
    return resp  # unreachable; satisfies type-checker


# ---------------------------------------------------------------------------
# Public client
# ---------------------------------------------------------------------------


class TTSClient:
    """
    Async SmartFlo TTS client.

    Create one instance at app startup and reuse it (e.g. via FastAPI lifespan).
    All methods handle token management transparently.
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.tts_base_url,
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "TTSClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------ auth

    async def ensure_authenticated(self) -> None:
        """Force a login check; useful to call once at startup."""
        await _ensure_token(self._client)

    async def logout(self) -> None:
        global _token, _token_expires_at
        if _token is None:
            return
        try:
            await self._client.delete(
                "/v1/auth/logout",
                headers=_auth_headers(),
            )
        except Exception:
            pass
        finally:
            _token = None
            _token_expires_at = 0.0

    # ------------------------------------------------------------------ CDRs

    async def get_cdrs(
        self,
        from_date: str,
        to_date: str,
        *,
        direction: str | None = None,
        call_type: str | None = None,
        agents: list[str] | None = None,
        call_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Fetch all CDRs for the given date range, paginating automatically.

        Args:
            from_date: Start of range, "YYYY-MM-DD HH:MM:SS"
            to_date:   End of range,   "YYYY-MM-DD HH:MM:SS"
            direction: "inbound" | "outbound" | None (both)
            call_type: "c" (answered) | "m" (missed) | None (both)
            agents:    Filter to specific agents, each formatted as "agent|<id>"
            call_id:   Fetch a single call by ID
            limit:     Page size (max ~100 recommended by TTS)

        Returns:
            Flat list of all CDR result dicts across all pages.
        """
        params: dict[str, Any] = {
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit,
        }
        if direction:
            params["direction"] = direction
        if call_type:
            params["call_type"] = call_type
        if agents:
            # httpx serialises list values as repeated keys: agents[]=v1&agents[]=v2
            params["agents[]"] = agents
        if call_id:
            params["call_id"] = call_id

        all_results: list[dict[str, Any]] = []
        page = 1

        while True:
            params["page"] = page
            resp = await _request(self._client, "GET", "/v1/call/records", params=params)
            results: list[dict[str, Any]] = resp.json().get("results", [])
            if not results:
                break
            all_results.extend(results)
            page += 1

        return all_results

    # ------------------------------------------------------------------ users

    async def get_users(self) -> list[dict[str, Any]]:
        """Return all agents/users from the TTS users endpoint."""
        resp = await _request(self._client, "GET", "/v1/users")
        data = resp.json()
        # Normalise: API may return a plain list or {"results": [...]}
        if isinstance(data, list):
            return data
        return data.get("results", [])

    # ------------------------------------------------------------------ live calls

    async def get_live_calls(self) -> list[dict[str, Any]]:
        """Return currently active/live calls."""
        resp = await _request(self._client, "GET", "/v1/live_calls")
        data = resp.json()
        if isinstance(data, list):
            return data
        return data.get("results", [])

    # ------------------------------------------------------------------ recordings

    async def download_recording(self, recording_url: str) -> bytes:
        """
        Download recording audio as raw bytes.

        Recording URLs are short-lived signed URLs — callers must invoke this
        immediately after obtaining the URL and must NOT cache the URL itself.
        Uses a separate client call (absolute URL, longer timeout).
        """
        # Signed URLs often don't need auth; try without first.
        resp = await self._client.get(recording_url, timeout=120.0)
        if resp.status_code == 401:
            resp = await self._client.get(
                recording_url,
                headers=_auth_headers(),
                timeout=120.0,
            )
        resp.raise_for_status()
        return resp.content


# ---------------------------------------------------------------------------
# Module-level singleton — import this in routers
# ---------------------------------------------------------------------------

tts_client = TTSClient()
