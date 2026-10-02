"""Error taxonomy mapped to HTTP codes (docs 8, 14.4)."""

from __future__ import annotations

from fastapi import status


class ServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class UnsupportedLanguageError(ServiceError):
    def __init__(self, language: str) -> None:
        super().__init__(
            "unsupported_language",
            f"no engine registered for language {language!r}",
            status.HTTP_400_BAD_REQUEST,
        )


class InputTooLongError(ServiceError):
    def __init__(self, limit: int) -> None:
        super().__init__(
            "input_too_long",
            f"text exceeds the maximum length of {limit} characters",
            status.HTTP_413_CONTENT_TOO_LARGE,
        )


class InvalidInputError(ServiceError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid_input", message, status.HTTP_422_UNPROCESSABLE_ENTITY)
