"""TraceGuard: graph-powered investigation assistant on synthetic data.

Auth is Application Default Credentials only (BR-008): the Cloud Run runtime service account
in production, `gcloud auth application-default login` locally. No API keys.
"""

import logging

import streamlit as st

from traceguard.ui.diagnostics import render_diagnostics
from traceguard.ui.models import CaseView, load_cases
from traceguard.ui.page import render_case_page, render_case_queue

logging.basicConfig(level=logging.INFO)


@st.cache_resource
def _cases() -> tuple[CaseView, ...]:
    return load_cases()


def main() -> None:
    st.set_page_config(page_title="TraceGuard", page_icon="🔎", layout="wide")
    st.title("TraceGuard")
    st.caption("Investigation aid on synthetic data · not a decision system · flags come from deterministic rules")
    view = render_case_queue(_cases())
    render_diagnostics()
    render_case_page(view)


main()
