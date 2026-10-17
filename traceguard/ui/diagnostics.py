"""Deployment check (TASK-001): one live Gemini call, labelled as live (BR-006)."""

import streamlit as st
from google import genai

from traceguard.ai.errors import InvestigationError
from traceguard.ai.gemini import GeminiConfig, build_client, generate_text

SMOKE_PROMPT = (
    "In two sentences, explain what a fraud operations analyst means by 'rapid forwarding' "
    "of funds between accounts. Do not name or accuse any person."
)


@st.cache_resource
def _client(config: GeminiConfig) -> genai.Client:
    return build_client(config)


def render_diagnostics() -> None:
    with st.sidebar.expander("Diagnostics"):
        try:
            config = GeminiConfig.from_env()
        except InvestigationError as exc:
            st.error(exc.user_message)
            return
        st.caption(f"Model `{config.model}` · location `{config.location}`")
        if not st.button("Call Gemini"):
            return
        try:
            with st.spinner("Calling Gemini on Vertex AI…"):
                text = generate_text(_client(config), config.model, SMOKE_PROMPT)
        except InvestigationError as exc:
            st.error(exc.user_message)
            return
        st.success("Live response from Gemini (not cached)")
        st.write(text or "(empty response)")
