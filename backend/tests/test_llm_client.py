"""Tests for the LLM resilience layer: the primary/fallback model chain,
and generate_content's retry-then-fallback behavior. The real Gemini API
is never called here - google.genai's client is mocked out, since these
tests are about our own retry/fallback logic, not Google's service."""

from types import SimpleNamespace

import pytest
from google.genai import errors as genai_errors

from app.core import llm_client


@pytest.fixture(autouse=True)
def reset_client_singleton():
    # generate_content lazily creates a module-level client singleton;
    # make sure each test starts clean rather than reusing whatever a
    # previous test set up.
    llm_client._client = None
    yield
    llm_client._client = None


class TestModelChain:

    def test_primary_model_comes_first(self, monkeypatch):
        monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL", "models/primary")
        monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL_FALLBACKS", "models/fallback")

        assert llm_client._model_chain() == ["models/primary", "models/fallback"]

    def test_duplicate_models_are_not_repeated(self, monkeypatch):
        monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL", "models/same")
        monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL_FALLBACKS", "models/same,models/other")

        assert llm_client._model_chain() == ["models/same", "models/other"]

    def test_empty_fallback_list_still_returns_the_primary(self, monkeypatch):
        monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL", "models/only-one")
        monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL_FALLBACKS", "")

        assert llm_client._model_chain() == ["models/only-one"]


def _fake_response(text="ok", total_tokens=10):
    return SimpleNamespace(
        text=text,
        usage_metadata=SimpleNamespace(
            prompt_token_count=total_tokens - 2,
            candidates_token_count=2,
            total_token_count=total_tokens,
        ),
    )


class TestGenerateContentFallback:

    def test_a_quota_error_on_the_primary_falls_through_to_the_fallback_model(
        self, monkeypatch, mocker
    ):
        monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL", "models/primary")
        monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL_FALLBACKS", "models/fallback")

        call_log = []

        def fake_generate_content(model, contents):
            call_log.append(model)
            if model == "models/primary":
                raise genai_errors.ClientError(429, {"error": {"message": "quota exceeded"}}, None)
            return _fake_response("answer from fallback")

        mock_client = mocker.Mock()
        mock_client.models.generate_content.side_effect = fake_generate_content
        mocker.patch.object(llm_client, "get_client", return_value=mock_client)

        result = llm_client.generate_content("hello", purpose="test")

        assert result == "answer from fallback"
        assert call_log == ["models/primary", "models/fallback"]

    def test_a_server_overload_retries_the_same_model_before_giving_up(
        self, monkeypatch, mocker
    ):
        monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL", "models/flaky")
        monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL_FALLBACKS", "")
        mocker.patch("time.sleep")  # don't actually wait during the test

        call_log = []

        def fake_generate_content(model, contents):
            call_log.append(model)
            if len(call_log) == 1:
                raise genai_errors.ServerError(503, {"error": {"message": "overloaded"}}, None)
            return _fake_response("answer after retry")

        mock_client = mocker.Mock()
        mock_client.models.generate_content.side_effect = fake_generate_content
        mocker.patch.object(llm_client, "get_client", return_value=mock_client)

        result = llm_client.generate_content("hello", purpose="test", retries_per_model=2)

        assert result == "answer after retry"
        assert call_log == ["models/flaky", "models/flaky"]

    def test_when_every_model_fails_the_last_error_is_raised(self, monkeypatch, mocker):
        monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL", "models/primary")
        monkeypatch.setattr(llm_client.settings, "GEMINI_MODEL_FALLBACKS", "models/fallback")

        mock_client = mocker.Mock()
        mock_client.models.generate_content.side_effect = genai_errors.ClientError(
            429, {"error": {"message": "quota exceeded"}}, None
        )
        mocker.patch.object(llm_client, "get_client", return_value=mock_client)

        with pytest.raises(genai_errors.ClientError):
            llm_client.generate_content("hello", purpose="test")


class TestOllamaProvider:
    """The Ollama HTTP integration, mocked - proves the request/response
    handling and retry logic are correct without requiring a real,
    multi-GB local model running in CI or this environment."""

    def test_provider_switch_routes_to_ollama_instead_of_gemini(self, monkeypatch, mocker):
        monkeypatch.setattr(llm_client.settings, "LLM_PROVIDER", "ollama")
        monkeypatch.setattr(llm_client.settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setattr(llm_client.settings, "OLLAMA_MODEL", "llama3.1:8b")

        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "response": "answer from local model",
            "prompt_eval_count": 12,
            "eval_count": 8,
        }
        mock_response.raise_for_status = mocker.Mock()
        mock_post = mocker.patch.object(llm_client.requests, "post", return_value=mock_response)

        result = llm_client.generate_content("hello", purpose="test")

        assert result == "answer from local model"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.args[0] == "http://localhost:11434/api/generate"
        assert call_kwargs.kwargs["json"]["model"] == "llama3.1:8b"
        assert call_kwargs.kwargs["json"]["prompt"] == "hello"

    def test_ollama_unreachable_retries_then_raises_a_clear_error(self, monkeypatch, mocker):
        monkeypatch.setattr(llm_client.settings, "LLM_PROVIDER", "ollama")
        monkeypatch.setattr(llm_client.settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setattr(llm_client.settings, "OLLAMA_MODEL", "llama3.1:8b")
        mocker.patch("time.sleep")

        import requests as requests_module
        mocker.patch.object(
            llm_client.requests, "post",
            side_effect=requests_module.ConnectionError("connection refused")
        )

        with pytest.raises(ConnectionError, match="Could not reach Ollama"):
            llm_client.generate_content("hello", purpose="test", retries_per_model=2)

    def test_ollama_recovers_after_a_transient_failure(self, monkeypatch, mocker):
        monkeypatch.setattr(llm_client.settings, "LLM_PROVIDER", "ollama")
        monkeypatch.setattr(llm_client.settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setattr(llm_client.settings, "OLLAMA_MODEL", "llama3.1:8b")
        mocker.patch("time.sleep")

        import requests as requests_module

        mock_response = mocker.Mock()
        mock_response.json.return_value = {"response": "recovered answer"}
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch.object(
            llm_client.requests, "post",
            side_effect=[requests_module.ConnectionError("first attempt failed"), mock_response]
        )

        result = llm_client.generate_content("hello", purpose="test", retries_per_model=2)
        assert result == "recovered answer"
