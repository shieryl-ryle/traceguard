"""Readable investigation errors (F-009). The UI shows `user_message`; logs get `kind` only."""

from typing import Literal

ErrorKind = Literal[
    "config",
    "credentials",
    "timeout",
    "permission",
    "not_found",
    "quota",
    "api",
    "payload_too_large",
    "too_many_rounds",
    "validation",
    "unexpected",
]


class InvestigationError(Exception):
    def __init__(self, kind: ErrorKind, user_message: str) -> None:
        super().__init__(user_message)
        self.kind = kind
        self.user_message = user_message


def api_error_message(code: int | None) -> tuple[ErrorKind, str]:
    if code == 403:
        return "permission", (
            "The service is not allowed to call Gemini (permission denied). "
            "Check the runtime service account roles."
        )
    if code == 404:
        return "not_found", (
            "The configured Gemini model was not found in this location. "
            "Check GEMINI_MODEL and VERTEX_LOCATION."
        )
    if code == 429:
        return "quota", "Gemini quota is exhausted for now. Wait a minute and try again."
    return "api", f"Gemini returned an error (HTTP {code}). Try again shortly."
