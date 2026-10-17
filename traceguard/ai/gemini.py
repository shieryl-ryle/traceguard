"""Gemini on Vertex AI via google-genai, ADC only (BR-008), bounded by a timeout (BR-007)."""

import logging
import os
from dataclasses import dataclass

import httpx
from google import genai
from google.auth.exceptions import DefaultCredentialsError, RefreshError
from google.genai import errors, types

from traceguard.ai.errors import InvestigationError, api_error_message
from traceguard.ai.schema import ModelBrief

REQUEST_TIMEOUT_MS = 30_000  # BR-007, provisional (PRD Q6). google-genai timeouts are in ms.
REQUIRED_ENV = ("GOOGLE_CLOUD_PROJECT", "VERTEX_LOCATION", "GEMINI_MODEL")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeminiConfig:
    project: str
    location: str
    model: str

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
        if missing:
            raise InvestigationError("config", f"Missing environment variables: {', '.join(missing)}")
        return cls(
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.environ["VERTEX_LOCATION"],
            model=os.environ["GEMINI_MODEL"],
        )


def build_client(config: GeminiConfig) -> genai.Client:
    # No retry_options: google-genai then makes exactly one attempt, so the timeout is the real cap.
    return genai.Client(
        vertexai=True,
        project=config.project,
        location=config.location,
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
    )


class GeminiBriefGenerator:
    """Returns the raw JSON text of a brief. Parsing and validation happen in `investigate`."""

    def __init__(self, config: GeminiConfig, client: genai.Client | None = None) -> None:
        self.model = config.model
        self._client = client or build_client(config)

    def __call__(self, system_instruction: str, user_prompt: str) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=ModelBrief,
            temperature=0.2,
        )
        try:
            response = self._client.models.generate_content(
                model=self.model, contents=user_prompt, config=config
            )
        except (DefaultCredentialsError, RefreshError) as exc:
            raise InvestigationError(
                "credentials",
                "Google Cloud credentials are missing or expired. Locally, run "
                "`gcloud auth application-default login`; on Cloud Run, check the runtime service account.",
            ) from exc
        except httpx.TimeoutException as exc:
            logger.warning("Gemini request timed out after %s ms", REQUEST_TIMEOUT_MS)
            raise InvestigationError(
                "timeout", f"Gemini did not respond within {REQUEST_TIMEOUT_MS // 1000} seconds. Try again."
            ) from exc
        except httpx.TransportError as exc:
            logger.warning("Gemini network error: %s", type(exc).__name__)
            raise InvestigationError("api", "Could not reach Gemini (network error). Try again shortly.") from exc
        except errors.APIError as exc:
            logger.warning("Gemini API error: code=%s status=%s", exc.code, exc.status)
            kind, message = api_error_message(exc.code)
            raise InvestigationError(kind, message) from exc
        except Exception as exc:
            logger.exception("Unexpected error calling Gemini")
            raise InvestigationError("unexpected", "Something went wrong calling Gemini. Check the service logs.") from exc
        return response.text or ""
