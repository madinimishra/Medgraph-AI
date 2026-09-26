import time

import requests
from google import genai
from google.genai import errors as genai_errors

from app.core.config import settings
from app.core import observability

_client = None


def get_client() -> genai.Client:
    global _client

    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)

    return _client


def _model_chain() -> list[str]:
    """Primary model first, then the configured fallback model(s) if the
    primary is unavailable (quota exhausted / overloaded). Deduplicated,
    order preserved."""

    models = [settings.GEMINI_MODEL] + [
        m.strip()
        for m in settings.GEMINI_MODEL_FALLBACKS.split(",")
        if m.strip()
    ]

    seen = set()
    ordered = []
    for m in models:
        if m not in seen:
            seen.add(m)
            ordered.append(m)

    return ordered


def _generate_with_gemini(prompt: str, purpose: str, retries_per_model: int, backoff_seconds: float) -> str:
    """Call Gemini with resilience on two axes:
    - transient overload (503): retried on the same model with backoff.
    - quota exhaustion (429) or repeated failure: falls through to the
      next model in settings.GEMINI_MODEL_FALLBACKS.

    Every call (success or not) is timed, and successful calls log
    token usage + which model actually served the request, via
    app.core.observability.
    """

    client = get_client()
    last_error = None
    model_chain = _model_chain()

    for index, model in enumerate(model_chain):
        for attempt in range(retries_per_model):

            t0 = time.time()
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                latency = time.time() - t0

                usage = response.usage_metadata
                observability.record_llm_call(
                    model=model,
                    purpose=purpose,
                    latency_seconds=latency,
                    prompt_tokens=usage.prompt_token_count if usage else None,
                    completion_tokens=usage.candidates_token_count if usage else None,
                    total_tokens=usage.total_token_count if usage else None,
                    fallback_used=(index > 0),
                )

                return response.text.strip()

            except genai_errors.ServerError as e:
                last_error = e
                if attempt < retries_per_model - 1:
                    time.sleep(backoff_seconds * (attempt + 1))

            except genai_errors.ClientError as e:
                last_error = e
                break  # quota/4xx - move to next model, don't retry same one

    raise last_error


def _generate_with_ollama(prompt: str, purpose: str, retries_per_model: int, backoff_seconds: float) -> str:
    """Call a locally-run model via Ollama's REST API - no data leaves
    the machine running Ollama. Same retry pattern as the Gemini path,
    since a local model server can also be transiently unavailable
    (still starting up, briefly out of memory, etc.)."""

    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    last_error = None

    for attempt in range(retries_per_model):
        t0 = time.time()
        try:
            response = requests.post(
                url,
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=120,
            )
            response.raise_for_status()
            latency = time.time() - t0

            data = response.json()
            text = data.get("response", "").strip()

            observability.record_llm_call(
                model=f"ollama/{settings.OLLAMA_MODEL}",
                purpose=purpose,
                latency_seconds=latency,
                prompt_tokens=data.get("prompt_eval_count"),
                completion_tokens=data.get("eval_count"),
                total_tokens=(
                    (data.get("prompt_eval_count") or 0) + (data.get("eval_count") or 0)
                ) or None,
                fallback_used=False,
            )

            return text

        except requests.RequestException as e:
            last_error = e
            if attempt < retries_per_model - 1:
                time.sleep(backoff_seconds * (attempt + 1))

    raise ConnectionError(
        f"Could not reach Ollama at {url} (model={settings.OLLAMA_MODEL}). "
        f"Is `ollama serve` running? Last error: {last_error}"
    )


def generate_content(
    prompt: str,
    purpose: str = "unknown",
    retries_per_model: int = 2,
    backoff_seconds: float = 2.0
) -> str:
    """Single entry point every agent in this app calls to reach an
    LLM. Which provider actually serves the request is a config switch
    (settings.LLM_PROVIDER), not a code change in any caller - this is
    what makes "run fully on local/self-hosted infrastructure, no data
    leaves the building" a deployment decision instead of a rewrite.
    See docs/PATH_TO_PRODUCTION.md.
    """

    if settings.LLM_PROVIDER == "ollama":
        return _generate_with_ollama(prompt, purpose, retries_per_model, backoff_seconds)

    return _generate_with_gemini(prompt, purpose, retries_per_model, backoff_seconds)
