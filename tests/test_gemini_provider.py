import json
import pytest
import sys
from pathlib import Path
from httpx import AsyncClient, MockTransport, Response, TimeoutException

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.providers.gemini import GeminiProvider, GeminiUnavailableError
from app.providers.factory import ProviderFactory
from app.providers.base import ProviderCapability, DataClassification
from app.core.config import settings


@pytest.mark.asyncio
async def test_gemini_capabilities_exclude_actions():
    provider = GeminiProvider(api_key="mock-gemini-key")
    assert provider.supports(ProviderCapability.SUMMARIZE) is True
    assert provider.supports(ProviderCapability.CLASSIFY) is True
    assert provider.supports(ProviderCapability.REASON) is True
    assert provider.supports(ProviderCapability.STRUCTURED_OUTPUT) is True
    # Crucial security guarantee: semantic interpretation only, never action execution
    assert provider.supports(ProviderCapability.GENERATE_ACTIONS) is False


@pytest.mark.asyncio
async def test_gemini_provider_success():
    def gemini_handler(request):
        assert "key=test-valid-key" in str(request.url)
        body = json.loads(request.content)
        assert "contents" in body
        return Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": json.dumps({
                                        "what_changed": "Phase 3 clinical trial readout shows zero annualized bleeds.",
                                        "why_it_matters": "Demonstrates non-inferiority to standard prophylactic regimens.",
                                        "primary_function": "MEDICAL_AFFAIRS",
                                        "suggested_action": "Update clinical briefing dossier for upcoming advisory committee.",
                                    })
                                }
                            ]
                        },
                        "finishReason": "STOP",
                    }
                ]
            },
        )

    provider = GeminiProvider(api_key="test-valid-key", max_retries=1)
    provider._client = AsyncClient(transport=MockTransport(gemini_handler))

    result = await provider.generate_intelligence(
        evidence=["Clinical trial NCT04561234 demonstrated 0 bleeds"],
        task="Analyze trial efficacy",
        classification=DataClassification.PUBLIC,
    )

    assert result["what_changed"] == "Phase 3 clinical trial readout shows zero annualized bleeds."
    assert result["why_it_matters"] == "Demonstrates non-inferiority to standard prophylactic regimens."
    assert result["primary_function"] == "MEDICAL_AFFAIRS"
    assert "suggested_action" in result

    meta = result["model_metadata"]
    assert meta["provider"] == "gemini"
    assert meta["mode"] == "reasoning"
    assert meta["reasoning_available"] is True
    assert meta["actions_available"] is False
    assert meta["fallback_used"] is True


@pytest.mark.asyncio
async def test_gemini_provider_missing_key():
    provider = GeminiProvider(api_key="")
    with pytest.raises(GeminiUnavailableError, match="No GEMINI_API_KEY configured"):
        await provider.generate_intelligence(
            evidence=["Evidence text"],
            task="Task",
            classification=DataClassification.PUBLIC,
        )


@pytest.mark.asyncio
async def test_gemini_privacy_gate_allows_public_and_synthetic():
    provider = GeminiProvider(api_key="mock-key")
    assert provider.validate_privacy_gate(DataClassification.PUBLIC) is True
    assert provider.validate_privacy_gate(DataClassification.SYNTHETIC) is True


@pytest.mark.asyncio
async def test_gemini_privacy_gate_blocks_confidential_and_patient_identifiable():
    provider = GeminiProvider(api_key="mock-key")
    assert provider.validate_privacy_gate(DataClassification.CONFIDENTIAL) is False
    assert provider.validate_privacy_gate(DataClassification.PATIENT_IDENTIFIABLE) is False
    assert provider.validate_privacy_gate(DataClassification.INTERNAL) is False
    assert provider.validate_privacy_gate(DataClassification.UNKNOWN) is False

    with pytest.raises(PermissionError, match="Privacy gate rejected external API transmission"):
        await provider.generate_intelligence(
            evidence=["Some clean text"],
            task="Task",
            classification=DataClassification.PATIENT_IDENTIFIABLE,
        )


@pytest.mark.asyncio
async def test_gemini_pii_in_evidence_raises_permission_error():
    provider = GeminiProvider(api_key="mock-key")
    with pytest.raises(PermissionError, match="PII/PHI detected in evidence"):
        await provider.generate_intelligence(
            evidence=["Patient Name: John Doe Subject ID: #SUB-9988"],
            task="Task",
            classification=DataClassification.PUBLIC,
        )


@pytest.mark.asyncio
async def test_gemini_provider_rate_limit_429_exhaustion():
    call_count = 0

    def rate_limit_handler(request):
        nonlocal call_count
        call_count += 1
        return Response(429, text="Resource has been exhausted (quota exceeded)")

    provider = GeminiProvider(api_key="test-key", max_retries=1)
    provider._client = AsyncClient(transport=MockTransport(rate_limit_handler))

    with pytest.raises(GeminiUnavailableError, match="Gemini API rate limit or server error"):
        await provider.generate_intelligence(
            evidence=["Public evidence text"],
            task="Task",
            classification=DataClassification.PUBLIC,
        )

    assert call_count == 2  # 1 initial + 1 retry


@pytest.mark.asyncio
async def test_gemini_provider_timeout_exhaustion():
    call_count = 0

    def timeout_handler(request):
        nonlocal call_count
        call_count += 1
        raise TimeoutException("Connection timed out waiting for Gemini")

    provider = GeminiProvider(api_key="test-key", max_retries=1)
    provider._client = AsyncClient(transport=MockTransport(timeout_handler))

    with pytest.raises(GeminiUnavailableError, match="Gemini API network timeout exhausted retries"):
        await provider.generate_intelligence(
            evidence=["Public evidence text"],
            task="Task",
            classification=DataClassification.PUBLIC,
        )

    assert call_count == 2


@pytest.mark.asyncio
async def test_gemini_provider_malformed_json_rejected():
    def malformed_handler(request):
        return Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "This is plain text, not valid JSON object"}
                            ]
                        }
                    }
                ]
            },
        )

    provider = GeminiProvider(api_key="test-key", max_retries=0)
    provider._client = AsyncClient(transport=MockTransport(malformed_handler))

    with pytest.raises(GeminiUnavailableError, match="Gemini response was not valid JSON"):
        await provider.generate_intelligence(
            evidence=["Public evidence text"],
            task="Task",
            classification=DataClassification.PUBLIC,
        )


@pytest.mark.asyncio
async def test_gemini_provider_missing_what_changed_rejected():
    def missing_field_handler(request):
        return Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": json.dumps({
                                        "why_it_matters": "Only why matters",
                                        "primary_function": "MEDICAL_AFFAIRS",
                                    })
                                }
                            ]
                        }
                    }
                ]
            },
        )

    provider = GeminiProvider(api_key="test-key", max_retries=0)
    provider._client = AsyncClient(transport=MockTransport(missing_field_handler))

    with pytest.raises(GeminiUnavailableError, match="missing required 'what_changed'"):
        await provider.generate_intelligence(
            evidence=["Public evidence text"],
            task="Task",
            classification=DataClassification.PUBLIC,
        )


@pytest.mark.asyncio
async def test_gemini_generate_summary_success():
    def summary_handler(request):
        return Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "Concise factual summary of haemophilia trial."}
                            ]
                        }
                    }
                ]
            },
        )

    provider = GeminiProvider(api_key="test-key", max_retries=0)
    provider._client = AsyncClient(transport=MockTransport(summary_handler))

    summary = await provider.generate_summary(
        text="Long text describing clinical endpoints...",
        classification=DataClassification.PUBLIC,
    )
    assert summary == "Concise factual summary of haemophilia trial."


@pytest.mark.asyncio
async def test_factory_routes_to_gemini_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "none")
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "mock-gemini-key")

    factory = ProviderFactory()

    def gemini_handler(request):
        return Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": json.dumps({
                                        "what_changed": "Gemini intelligence generated.",
                                        "why_it_matters": "Cloud adapter active.",
                                        "primary_function": "REGULATORY",
                                        "suggested_action": "File regulatory update.",
                                    })
                                }
                            ]
                        }
                    }
                ]
            },
        )

    factory.gemini._client = AsyncClient(transport=MockTransport(gemini_handler))

    result = await factory.execute_task(
        required_capability=ProviderCapability.REASON,
        evidence=["Clinical evidence"],
        task="Evaluate regulatory impact",
        classification=DataClassification.PUBLIC,
    )

    meta = result["model_metadata"]
    assert meta["provider"] == "gemini"
    assert meta["mode"] == "reasoning"


@pytest.mark.asyncio
async def test_factory_gemini_failure_falls_through_to_degraded(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "none")
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "mock-gemini-key")
    monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", False)

    factory = ProviderFactory()

    def error_handler(request):
        return Response(503, text="Gemini service unavailable")

    factory.gemini.max_retries = 0
    factory.gemini._client = AsyncClient(transport=MockTransport(error_handler))

    result = await factory.execute_task(
        required_capability=ProviderCapability.REASON,
        evidence=["Clinical evidence point 1"],
        task="Evaluate regulatory impact",
        classification=DataClassification.PUBLIC,
    )

    meta = result["model_metadata"]
    assert meta["provider"] == "bart"
    assert meta["mode"] == "degraded_factual"
    assert meta["reasoning_available"] is False
