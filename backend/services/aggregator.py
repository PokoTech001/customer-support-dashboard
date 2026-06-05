"""
Analytics aggregation over raw CDR dicts returned by tts_client.

All functions are pure (no I/O) and operate on the list[dict] shape that
tts_client.get_cdrs() returns.
"""

from collections import defaultdict

from models.schemas import (
    AgentAnalyticsResponse,
    AgentMetrics,
    DailyBucket,
    HourlyBucket,
    OverallAnalyticsResponse,
)


# ---------------------------------------------------------------------------
# Field-extraction helpers
# ---------------------------------------------------------------------------


def _status(cdr: dict) -> str:
    return (cdr.get("status") or "").strip().lower()


def _dialer_details(cdr: dict) -> dict:
    return cdr.get("dialer_call_details") or {}


def _is_sla_met(cdr: dict) -> bool:
    val = _dialer_details(cdr).get("sla_status")
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.strip().lower() in ("met", "yes", "true", "1")
    return False


def _is_fcr(cdr: dict) -> bool:
    val = _dialer_details(cdr).get("first_call_resolution")
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.strip().lower() in ("yes", "true", "1")
    return False


def _hour_from_time(time_str: str) -> int | None:
    """Parse "HH:MM:SS" → hour int, or None on malformed input."""
    try:
        return int(time_str.split(":")[0])
    except (AttributeError, ValueError, IndexError):
        return None


def _pct(numerator: int, denominator: int) -> float:
    return round(numerator / denominator * 100, 1) if denominator else 0.0


def _avg(values: list[int | float]) -> float:
    return round(sum(values) / len(values), 1) if values else 0.0


# ---------------------------------------------------------------------------
# Public aggregation functions
# ---------------------------------------------------------------------------


def compute_overall(cdrs: list[dict]) -> OverallAnalyticsResponse:
    """
    Aggregate a flat list of CDRs into overall analytics.

    hourly_distribution always contains all 24 hours (0–23) so the frontend
    can render a complete chart even when some hours have zero calls.
    daily_distribution contains one entry per calendar date present in the data.
    """
    hourly: dict[int, dict[str, int]] = {h: {"answered": 0, "missed": 0} for h in range(24)}
    daily: dict[str, dict[str, int]] = defaultdict(lambda: {"answered": 0, "missed": 0})

    answered = missed = 0
    handle_times: list[int] = []
    talk_times: list[int] = []
    sla_total = sla_met = 0

    for cdr in cdrs:
        is_answered = _status(cdr) == "answered"

        if is_answered:
            answered += 1
        else:
            missed += 1

        # Hourly bucket
        hour = _hour_from_time(cdr.get("time", ""))
        if hour is not None and 0 <= hour < 24:
            hourly[hour]["answered" if is_answered else "missed"] += 1

        # Daily bucket
        date = (cdr.get("date") or "").strip()
        if date:
            daily[date]["answered" if is_answered else "missed"] += 1

        # Duration metrics — only meaningful for answered calls
        if is_answered:
            duration = cdr.get("call_duration")
            talk = cdr.get("answered_seconds")
            if duration:
                handle_times.append(int(duration))
            if talk:
                talk_times.append(int(talk))

        # SLA — evaluated on all calls
        sla_total += 1
        if _is_sla_met(cdr):
            sla_met += 1

    return OverallAnalyticsResponse(
        total_inbound=answered + missed,
        answered=answered,
        missed=missed,
        answer_rate=_pct(answered, answered + missed),
        avg_handle_time=_avg(handle_times),
        avg_talk_time=_avg(talk_times),
        sla_compliance=_pct(sla_met, sla_total),
        hourly_distribution=[
            HourlyBucket(hour=h, **hourly[h]) for h in range(24)
        ],
        daily_distribution=[
            DailyBucket(date=d, **v) for d, v in sorted(daily.items())
        ],
    )


def compute_agent_metrics(cdrs: list[dict]) -> AgentAnalyticsResponse:
    """
    Aggregate CDRs into per-agent metrics, sorted alphabetically by agent name.
    """
    # Each agent accumulates mutable accumulators
    agents: dict[str, dict] = defaultdict(lambda: {
        "answered": 0,
        "missed": 0,
        "talk_times": [],
        "sla_total": 0,
        "sla_met": 0,
        "fcr_total": 0,
        "fcr_met": 0,
    })

    for cdr in cdrs:
        name = (cdr.get("agent_name") or "Unknown").strip()
        is_answered = _status(cdr) == "answered"
        a = agents[name]

        if is_answered:
            a["answered"] += 1
            talk = cdr.get("answered_seconds")
            if talk:
                a["talk_times"].append(int(talk))
        else:
            a["missed"] += 1

        a["sla_total"] += 1
        if _is_sla_met(cdr):
            a["sla_met"] += 1

        a["fcr_total"] += 1
        if _is_fcr(cdr):
            a["fcr_met"] += 1

    metrics = []
    for name, a in sorted(agents.items()):
        total = a["answered"] + a["missed"]
        metrics.append(
            AgentMetrics(
                agent_name=name,
                answered=a["answered"],
                missed=a["missed"],
                answer_rate=_pct(a["answered"], total),
                avg_talk_time=_avg(a["talk_times"]),
                first_call_resolution=_pct(a["fcr_met"], a["fcr_total"]),
                sla_compliance=_pct(a["sla_met"], a["sla_total"]),
            )
        )

    return AgentAnalyticsResponse(agents=metrics)
