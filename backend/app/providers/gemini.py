"""GeminiProvider — Google Gemini API client (Free Tier) (REQ-P15-07, REQ-P15-08, REQ-P15-09).

Strict privacy gate (``validate_privacy_gate``) is enforced before ANY external
transmission: only PUBLIC / SYNTHETIC payloads may reach Google Gemini.
Payloads containing PATIENT_IDENTIFIABLE, CONFIDENTIAL, INTERNAL, or UNKNOWN
data classifications are strictly rejected before transmission (addressing CONCERNS.md lines 9-11).
When no GEMINI_API_KEY is configured or the Gemini API fails/times out/rate-limits (429),
``GeminiUnavailableError`` is raised so ProviderFactory falls through to BART degraded mode.
Capabilities exclude GENERATE_ACTIONS: semantic interpretation only, never action execution.
"""

import asyncio
import json
import logging
import os
import random
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.base import LLMProvider, ProviderCapability, DataClassification
from app.schemas import ModelMetadataSchema
from app.services.pii import PIIPHIScrubber

logger = get_logger("gemini_provider")

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiUnavailableError(Exception):
    """Raised when the Gemini provider cannot execute (no key, 429, timeout, or API failure).

    Caught by ProviderFactory which falls through to BART degraded mode.
    """


class GeminiProvider(LLMProvider):
    name = "gemini"
    capabilities = [
        ProviderCapability.SUMMARIZE,
        ProviderCapability.CLASSIFY,
        ProviderCapability.REASON,
        ProviderCapability.STRUCTURED_OUTPUT,
    ]
    # NOTE: ProviderCapability.GENERATE_ACTIONS is deliberately omitted.
    # The cloud model performs semantic interpretation only, never action execution.

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_s: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self.api_key = api_key if api_key is not None else (settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY") or "")
        self.model_name = model_name or settings.GEMINI_MODEL
        self.timeout_s = timeout_s if timeout_s is not None else settings.GEMINI_TIMEOUT_S
        self.max_retries = max_retries if max_retries is not None else settings.GEMINI_MAX_RETRIES
        self._client: Optional[httpx.AsyncClient] = None

    async def aclose(self) -> None:
        """Gracefully closes the underlying HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _ensure_client(self) -> httpx.AsyncClient:
        """Lazily creates the Gemini HTTP client (connect=5s, read=timeout_s)."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_s, connect=5.0)
            )
        return self._client

    def validate_privacy_gate(self, classification: DataClassification) -> bool:
        """Mandatory Privacy Gate immediately before external transmission.

        Strictly enforces that ONLY DataClassification.PUBLIC and DataClassification.SYNTHETIC
        payloads can reach Google Gemini, explicitly blocking DataClassification.PATIENT_IDENTIFIABLE,
        CONFIDENTIAL, INTERNAL, and UNKNOWN (addressing CONCERNS.md lines 9-11).
        """
        key = self.api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if not key:
            logger.warning("Gemini execution blocked: Missing GEMINI_API_KEY")
            return False

        if classification in (DataClassification.PUBLIC, DataClassification.SYNTHETIC):
            return True

        logger.warning(
            "Gemini execution BLOCKED by Privacy Gate. Data classification: '%s' rejected.",
            classification,
        )
        return False

    async def _post_with_retry(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = True,
    ) -> str:
        key = self.api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise GeminiUnavailableError("No GEMINI_API_KEY configured")

        client = self._ensure_client()
        url = f"{GEMINI_API_BASE}/{self.model_name}:generateContent?key={key}"

        contents: List[Dict[str, Any]] = []
        if system_instruction:
            contents.append({
                "role": "user",
                "parts": [{"text": f"[SYSTEM INSTRUCTION]\n{system_instruction}\n[END SYSTEM INSTRUCTION]"}],
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I will strictly follow these instructions."}],
            })
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}],
        })

        generation_config: Dict[str, Any] = {
            "temperature": 0.2,
        }
        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        body = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        attempt = 0
        last_error: Optional[Exception] = None

        while attempt <= self.max_retries:
            try:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=body,
                )
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise GeminiUnavailableError("Gemini response contained no candidates (content filter or blocked)")
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts or "text" not in parts[0]:
                        raise GeminiUnavailableError("Gemini candidate contained no text parts")
                    return parts[0]["text"]

                # Check if retryable (408, 429, 5xx)
                status = response.status_code
                if status in (408, 429) or status >= 500:
                    if attempt < self.max_retries:
                        attempt += 1
                        backoff = (2.0 ** attempt) * 0.5 + random.uniform(0.1, 0.5)
                        logger.warning(
                            "Gemini API returned status %s. Retrying attempt %s/%s after %.2fs...",
                            status, attempt, self.max_retries, backoff
                        )
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        raise GeminiUnavailableError(
                            f"Gemini API rate limit or server error ({status}) exhausted retries: {response.text}"
                        )
                else:
                    raise GeminiUnavailableError(f"Gemini API client error ({status}): {response.text}")

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                last_error = net_err
                if attempt < self.max_retries:
                    attempt += 1
                    backoff = (2.0 ** attempt) * 0.5 + random.uniform(0.1, 0.5)
                    logger.warning(
                        "Gemini API network/timeout error: %s. Retrying attempt %s/%s after %.2fs...",
                        net_err, attempt, self.max_retries, backoff
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise GeminiUnavailableError(f"Gemini API network timeout exhausted retries: {net_err}") from net_err
            except GeminiUnavailableError:
                raise
            except Exception as e:
                raise GeminiUnavailableError(f"Gemini API invocation error: {e}") from e

        raise GeminiUnavailableError(f"Gemini API exhausted retries: {last_error}")

    async def generate_summary(
        self,
        text: str,
        classification: DataClassification = DataClassification.UNKNOWN,
    ) -> str:
        """Summarizes text via the Gemini generateContent REST API.

        Strictly enforces the privacy gate and scrubs all PII.
        """
        key = self.api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise GeminiUnavailableError("No GEMINI_API_KEY configured")

        if not self.validate_privacy_gate(classification):
            raise PermissionError(
                f"Privacy gate rejected external API transmission for classification '{classification}'"
            )

        scrubbed_text, has_pii, _ = PIIPHIScrubber.scrub(text)
        if has_pii:
            raise PermissionError("Privacy gate rejected payload: PII/PHI detected in text")

        prompt = f"Summarize the following evidence concisely and factually:\n\n{scrubbed_text}"
        return await self._post_with_retry(
            prompt=prompt,
            system_instruction="You are a precise medical intelligence summarizer.",
            json_mode=False,
        )

    async def generate_intelligence(
        self,
        evidence: List[str],
        task: str,
        classification: DataClassification = DataClassification.UNKNOWN,
    ) -> Dict[str, Any]:
        """Generates structured intelligence analysis via the Gemini REST API.

        Adheres strictly to the existing intent schema:
        what_changed, why_it_matters, primary_function, suggested_action, model_metadata.
        """
        key = self.api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise GeminiUnavailableError("No GEMINI_API_KEY configured")

        if not self.validate_privacy_gate(classification):
            raise PermissionError(
                f"Privacy gate rejected external API transmission for classification '{classification}'"
            )

        # Scrub all evidence items and ensure no PII
        scrubbed_evidence = []
        for item in evidence:
            scrubbed, has_pii, _ = PIIPHIScrubber.scrub(item)
            if has_pii:
                raise PermissionError("Privacy gate rejected payload: PII/PHI detected in evidence")
            scrubbed_evidence.append(scrubbed)

        start_time = time.time()
        evidence_block = "\n".join(f"- {e}" for e in scrubbed_evidence)
        system_prompt = (
            "You are a competitive intelligence analyst for a haemophilia market team. "
            "Analyze the provided public evidence and return STRICT JSON with exactly these "
            "keys: what_changed, why_it_matters, primary_function, suggested_action."
        )
        prompt = (
            f"Evidence:\n{evidence_block}\n\n"
            f"Task: {task}\n\n"
            "Return the JSON object only."
        )

        raw = await self._post_with_retry(
            prompt=prompt,
            system_instruction=system_prompt,
            json_mode=True,
        )
        latency = int((time.time() - start_time) * 1000)

        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as json_err:
            logger.warning("Gemini response was not valid JSON: %s", raw[:200])
            raise GeminiUnavailableError("Gemini response was not valid JSON") from json_err

        if not isinstance(parsed, dict):
            raise GeminiUnavailableError("Gemini response JSON was not a dictionary")

        # Validate presence of expected intent keys
        what_changed = parsed.get("what_changed")
        if not what_changed or not isinstance(what_changed, str):
            raise GeminiUnavailableError("Gemini response missing required 'what_changed' string")

        metadata = ModelMetadataSchema(
            provider="gemini",
            mode="reasoning",
            model=self.model_name,
            fallback_used=True,
            fallback_reason="gemma_offline_cloud_gemini",
            reasoning_available=True,
            actions_available=False,
            latency_ms=latency,
        )

        return {
            "what_changed": what_changed,
            "why_it_matters": parsed.get("why_it_matters", ""),
            "primary_function": parsed.get("primary_function", "MEDICAL_AFFAIRS"),
            "suggested_action": parsed.get(
                "suggested_action",
                "Suggested — requires human review: Prepare scientific FAQ for Medical Affairs.",
            ),
            "model_metadata": metadata.model_dump(),
        }
