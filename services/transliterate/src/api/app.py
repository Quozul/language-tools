"""FastAPI application (docs section 8). The API layer only validates input,
looks up an engine, and serializes output (docs 14.1)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from version import __version__
from api.errors import InputTooLongError, ServiceError, UnsupportedLanguageError
from api.schemas import (
    AnnotateRequest,
    AnnotateResponse,
    CapabilitiesResponse,
    CompactAnnotateResponse,
    to_compact_token_model,
    to_token_model,
)
from config import Settings, get_settings
from domain import EngineOptions
from engine import EngineRegistry
from ja import engine as ja_engine

logger = logging.getLogger("qzl")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    registry = EngineRegistry()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        registry.register(ja_engine.build(settings))
        app.state.ready = True
        logger.info("engines loaded: %s", ", ".join(registry.languages()))
        yield

    app = FastAPI(title="qzl-transliterate", version=__version__, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.registry = registry
    app.state.settings = settings
    app.state.ready = False

    @app.exception_handler(ServiceError)
    async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.get("/v1/health")
    def health() -> dict[str, object]:
        return {"status": "ok" if app.state.ready else "loading", "ready": app.state.ready}

    @app.get("/v1/capabilities")
    def capabilities() -> CapabilitiesResponse:
        engines: dict[str, dict[str, object]] = {}
        for lang in registry.languages():
            lang_engine = registry.get(lang)
            assert lang_engine is not None
            engines[lang] = {
                "engine": lang_engine.capabilities.engine,
                "engine_version": lang_engine.engine_version,
                "romanization_systems": list(lang_engine.capabilities.romanization_systems),
                "option_defaults": lang_engine.capabilities.option_defaults,
            }
        return CapabilitiesResponse(languages=list(registry.languages()), engines=engines)

    @app.post("/v1/annotate")
    def annotate(
        request: AnnotateRequest,
    ) -> AnnotateResponse | CompactAnnotateResponse:
        if len(request.text) > settings.max_text_length:
            raise InputTooLongError(settings.max_text_length)
        engine = registry.get(request.language)
        if engine is None:
            raise UnsupportedLanguageError(request.language)
        options = EngineOptions(
            romanization_system=request.romanization_system,
            long_vowel_style=request.long_vowel_style,
            include_ruby=request.include_ruby,
            include_alternatives=request.include_alternatives,
            word_spacing=request.word_spacing,
        )
        result = engine.annotate(request.text, options)
        if request.detail == "compact":
            return CompactAnnotateResponse(
                language=request.language,
                tokens=[to_compact_token_model(t) for t in result.tokens],
            )
        unknown = sum(1 for t in result.tokens if "unknown-word" in t.flags)
        low = sum(1 for t in result.tokens if t.confidence == "low")
        logger.info(
            "annotate lang=%s tokens=%d unknown=%d low_confidence=%d",
            request.language,
            len(result.tokens),
            unknown,
            low,
        )
        return AnnotateResponse(
            language=request.language,
            engine=engine.capabilities.engine,
            engine_version=engine.engine_version,
            romanization_system=options.romanization_system,
            options_applied=engine.capabilities.option_defaults
            | {
                "romanization_system": options.romanization_system,
                "long_vowel_style": options.long_vowel_style,
                "include_ruby": options.include_ruby,
                "include_alternatives": options.include_alternatives,
                "word_spacing": options.word_spacing,
            },
            tokens=[to_token_model(t) for t in result.tokens],
            warnings=list(result.warnings),
        )

    return app
