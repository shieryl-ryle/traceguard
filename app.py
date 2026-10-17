"""TraceGuard walking skeleton (TASK-001): one button -> live Gemini call on Vertex AI.

Auth is Application Default Credentials only (BR-008): the Cloud Run runtime service account
in production, `gcloud auth application-default login` locally. No API keys.
"""

import logging
import os

import httpx
import streamlit as st
from google import genai
from google.auth.exceptions import DefaultCredentialsError
from google.genai import errors, types

REQUEST_TIMEOUT_MS = 30_000  # BR-007, provisional (PRD Q6). google-genai timeouts are in ms.
REQUIRED_ENV = ("GOOGLE_CLOUD_PROJECT", "VERTEX_LOCATION", "GEMINI_MODEL")
SMOKE_PROMPT = (
    "In two sentences, explain what a fraud operations analyst means by 'rapid forwarding' "
    "of funds between accounts. Do not name or accuse any person."
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("traceguard")


def read_config() -> dict[str, str]:
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    return {name: os.environ[name] for name in REQUIRED_ENV}


@st.cache_resource
def get_client(project: str, location: str) -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=project,
        location=location,
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
    )


def describe_api_error(exc: errors.APIError) -> str:
    if exc.code == 403:
        return "The service is not allowed to call Gemini (permission denied). Check the runtime service account roles."
    if exc.code == 404:
        return "The configured Gemini model was not found in this location. Check GEMINI_MODEL and VERTEX_LOCATION."
    if exc.code == 429:
        return "Gemini quota is exhausted for now. Wait a minute and try again."
    return f"Gemini returned an error (HTTP {exc.code}). Try again shortly."


def main() -> None:
    st.set_page_config(page_title="TraceGuard", page_icon="🔎")
    st.title("TraceGuard")
    st.caption("Walking skeleton · synthetic data only · investigation aid, not a decision system")

    try:
        config = read_config()
    except RuntimeError as exc:
        st.error(str(exc))
        return

    st.write(f"Model: `{config['GEMINI_MODEL']}` · Location: `{config['VERTEX_LOCATION']}`")

    if not st.button("Call Gemini", type="primary"):
        return

    try:
        client = get_client(config["GOOGLE_CLOUD_PROJECT"], config["VERTEX_LOCATION"])
        with st.spinner("Calling Gemini on Vertex AI…"):
            response = client.models.generate_content(
                model=config["GEMINI_MODEL"],
                contents=SMOKE_PROMPT,
            )
    except DefaultCredentialsError:
        logger.warning("No Application Default Credentials available")
        st.error(
            "No Google Cloud credentials found. Locally, run "
            "`gcloud auth application-default login`; on Cloud Run, check the runtime service account."
        )
        return
    except httpx.TimeoutException:
        logger.warning("Gemini request timed out after %s ms", REQUEST_TIMEOUT_MS)
        st.error(f"Gemini did not respond within {REQUEST_TIMEOUT_MS // 1000} seconds. Try again.")
        return
    except errors.APIError as exc:
        logger.warning("Gemini API error: code=%s status=%s", exc.code, exc.status)
        st.error(describe_api_error(exc))
        return
    except Exception:
        logger.exception("Unexpected error calling Gemini")
        st.error("Something went wrong calling Gemini. Check the service logs.")
        return

    st.success("Live response from Gemini (not cached)")
    st.write(response.text or "(empty response)")


main()
