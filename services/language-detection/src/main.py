from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import fasttext
import pycountry
import regex
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import hf_hub_download
from pydantic import BaseModel, Field

MODEL_REPO_ID = "HPLT/OpenLID-v3"
MODEL_FILENAME = "openlid-v3.bin"

NONWORD_REPLACE_PATTERN = regex.compile(r"[^\p{Word}\p{Zs}]|\d")
SPACE_PATTERN = regex.compile(r"\s\s+")

_model = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    load_model()
    app.state.ready = True
    yield


app = FastAPI(title="Language Detection API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.ready = False


class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Input text to detect the language of")


class DetectResponse(BaseModel):
    language: str = Field(..., description="ISO 639-1 (2-letter) language code")
    confidence: float = Field(..., description="Model confidence score")


def load_model():
    global _model
    if _model is None:
        model_path = hf_hub_download(repo_id=MODEL_REPO_ID, filename=MODEL_FILENAME)
        _model = fasttext.load_model(model_path)
    return _model


def preprocess(text: str) -> str:
    text = text.strip().replace("\n", " ").lower()
    text = SPACE_PATTERN.sub(" ", text)
    text = NONWORD_REPLACE_PATTERN.sub("", text)
    return text


MACROLANGUAGE_FALLBACKS = {
    "cmn": "zh",
    "yue": "zh",
    "ars": "ar",
    "afb": "ar",
    "acm": "ar",
    "ary": "ar",
    "arb": "ar",
    "ajp": "ar",
    "apc": "ar",
    "ayl": "ar",
    "acx": "ar",
    "glk": "fa",
}


def to_iso_639_1(label: str) -> str:
    code = label.replace("__label__", "").split("_")[0]
    language = pycountry.languages.get(alpha_3=code)
    if language is not None and hasattr(language, "alpha_2"):
        return language.alpha_2
    return MACROLANGUAGE_FALLBACKS.get(code, code)


@app.get("/v1/health")
def health() -> dict[str, object]:
    return {"status": "ok" if app.state.ready else "loading", "ready": app.state.ready}


@app.post("/v1/detect", response_model=DetectResponse)
def detect(request: DetectRequest) -> DetectResponse:
    cleaned = preprocess(request.text)
    if not cleaned.strip():
        raise HTTPException(status_code=422, detail="Text contains no detectable content")
    labels, scores = load_model().predict(
        text=cleaned, k=1, threshold=0.0, on_unicode_error="strict"
    )
    if not labels:
        raise HTTPException(status_code=422, detail="Language could not be detected")
    return DetectResponse(
        language=to_iso_639_1(labels[0]),
        confidence=float(scores[0]),
    )
