"""Lightweight in-process observability for LLM calls: latency and
token usage per call, with simple aggregation. Kept in memory (capped)
rather than a full metrics stack - this is a project-scale system, not
a production deployment, so a bounded in-memory log is the honest
amount of infrastructure to build here."""

import time
import threading
from collections import deque

_MAX_ENTRIES = 500
_lock = threading.Lock()
_log = deque(maxlen=_MAX_ENTRIES)


def record_llm_call(
    model: str,
    purpose: str,
    latency_seconds: float,
    prompt_tokens: int = None,
    completion_tokens: int = None,
    total_tokens: int = None,
    fallback_used: bool = False,
):
    with _lock:
        _log.append({
            "timestamp": time.time(),
            "model": model,
            "purpose": purpose,
            "latency_seconds": round(latency_seconds, 3),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "fallback_used": fallback_used,
        })


def get_stats() -> dict:
    with _lock:
        entries = list(_log)

    if not entries:
        return {
            "call_count": 0,
            "avg_latency_seconds": None,
            "total_tokens": 0,
            "fallback_rate": None,
            "by_model": {},
            "by_purpose": {},
            "recent_calls": [],
        }

    total_tokens = sum(e["total_tokens"] or 0 for e in entries)
    avg_latency = sum(e["latency_seconds"] for e in entries) / len(entries)
    fallback_count = sum(1 for e in entries if e["fallback_used"])

    by_model = {}
    for e in entries:
        m = by_model.setdefault(e["model"], {"count": 0, "total_tokens": 0, "total_latency": 0.0})
        m["count"] += 1
        m["total_tokens"] += e["total_tokens"] or 0
        m["total_latency"] += e["latency_seconds"]

    for m in by_model.values():
        m["avg_latency_seconds"] = round(m["total_latency"] / m["count"], 3)
        del m["total_latency"]

    by_purpose = {}
    for e in entries:
        p = by_purpose.setdefault(e["purpose"], {"count": 0, "total_tokens": 0, "total_latency": 0.0})
        p["count"] += 1
        p["total_tokens"] += e["total_tokens"] or 0
        p["total_latency"] += e["latency_seconds"]

    for p in by_purpose.values():
        p["avg_latency_seconds"] = round(p["total_latency"] / p["count"], 3)
        del p["total_latency"]

    return {
        "call_count": len(entries),
        "avg_latency_seconds": round(avg_latency, 3),
        "total_tokens": total_tokens,
        "fallback_rate": round(fallback_count / len(entries), 3),
        "by_model": by_model,
        "by_purpose": by_purpose,
        "recent_calls": list(entries)[-20:],
    }
