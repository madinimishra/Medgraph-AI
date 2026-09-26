"""Tests for the in-process LLM call logging used to detect (and report)
when the fallback model served a request - this is what let us catch
the free-tier quota exhaustion in eval/comparison runs instead of
mistaking degraded model quality for a real capability gap."""

from app.core import observability


def _clear_log():
    observability._log.clear()


def test_get_stats_on_an_empty_log_does_not_crash():
    _clear_log()
    stats = observability.get_stats()
    assert stats["call_count"] == 0
    assert stats["fallback_rate"] is None


def test_a_single_recorded_call_is_reflected_in_the_stats():
    _clear_log()
    observability.record_llm_call(
        model="models/primary", purpose="cypher_generation",
        latency_seconds=1.5, prompt_tokens=100, completion_tokens=20,
        total_tokens=120, fallback_used=False,
    )

    stats = observability.get_stats()
    assert stats["call_count"] == 1
    assert stats["total_tokens"] == 120
    assert stats["fallback_rate"] == 0.0


def test_fallback_rate_reflects_the_proportion_of_fallback_calls():
    _clear_log()
    observability.record_llm_call(
        model="models/primary", purpose="x", latency_seconds=1,
        prompt_tokens=1, completion_tokens=1, total_tokens=2, fallback_used=False,
    )
    observability.record_llm_call(
        model="models/fallback", purpose="x", latency_seconds=1,
        prompt_tokens=1, completion_tokens=1, total_tokens=2, fallback_used=True,
    )

    stats = observability.get_stats()
    assert stats["call_count"] == 2
    assert stats["fallback_rate"] == 0.5


def test_the_log_is_capped_and_does_not_grow_without_bound():
    _clear_log()
    for i in range(observability._MAX_ENTRIES + 50):
        observability.record_llm_call(
            model="models/x", purpose="x", latency_seconds=0.1,
            prompt_tokens=1, completion_tokens=1, total_tokens=2, fallback_used=False,
        )

    assert len(observability._log) == observability._MAX_ENTRIES
