import logging

import httpx
from fastapi import APIRouter, HTTPException, Query

from models.schemas import AgentAnalyticsResponse, OverallAnalyticsResponse
from services.aggregator import compute_agent_metrics, compute_overall
from services.tts_client import tts_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calls", tags=["calls"])


def _handle_tts_error(exc: httpx.HTTPStatusError) -> HTTPException:
    logger.error("TTS API returned %d", exc.response.status_code)
    return HTTPException(
        status_code=502,
        detail=f"TTS API error: {exc.response.status_code}",
    )


@router.get("/overall", response_model=OverallAnalyticsResponse)
async def get_overall_analytics(
    from_date: str = Query(..., description='Start of range, format "YYYY-MM-DD HH:MM:SS"'),
    to_date: str = Query(..., description='End of range,   format "YYYY-MM-DD HH:MM:SS"'),
) -> OverallAnalyticsResponse:
    """
    Aggregate CDRs for the given date range into overall call analytics.

    Returns KPI totals, hourly distribution (all 24 hours), and daily distribution.
    """
    try:
        cdrs = await tts_client.get_cdrs(from_date=from_date, to_date=to_date)
    except httpx.HTTPStatusError as exc:
        raise _handle_tts_error(exc) from exc

    return compute_overall(cdrs)


@router.get("/agent", response_model=AgentAnalyticsResponse)
async def get_agent_analytics(
    from_date: str = Query(..., description='Start of range, format "YYYY-MM-DD HH:MM:SS"'),
    to_date: str = Query(..., description='End of range,   format "YYYY-MM-DD HH:MM:SS"'),
    agent_id: str | None = Query(
        None,
        description='Optional agent ID to filter to a single agent. Omit for all agents.',
    ),
) -> AgentAnalyticsResponse:
    """
    Per-agent breakdown of calls, talk time, FCR, and SLA for the given date range.

    Pass agent_id to restrict results to a single agent; omit for all agents.
    """
    agents_filter = [f"agent|{agent_id}"] if agent_id else None

    try:
        cdrs = await tts_client.get_cdrs(
            from_date=from_date,
            to_date=to_date,
            agents=agents_filter,
        )
    except httpx.HTTPStatusError as exc:
        raise _handle_tts_error(exc) from exc

    return compute_agent_metrics(cdrs)
