"""Authentication and AI client entry points."""

from .email_backend import (
    get_gemini_client,
    gmail_login,
    gmail_send_login,
)

__all__ = ["get_gemini_client", "gmail_login", "gmail_send_login"]
