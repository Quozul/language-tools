# syntax=docker/dockerfile:1
FROM alpine:3.20 AS downloader
ARG MIRROR_URL=https://files.quozul.dev/qzl-mirror
RUN mkdir /data \
    && wget -q -O /data/JmdictFurigana.json "$MIRROR_URL/JmdictFurigana.json" \
    && wget -q -O /data/JmnedictFurigana.json "$MIRROR_URL/JmnedictFurigana.json" \
    && wget -q -O /data/JmdictKanaExpressions.json "$MIRROR_URL/JmdictKanaExpressions.json" \
    && wget -q -O /unidic-3.1.0.zip "$MIRROR_URL/unidic-3.1.0.zip" \
    && printf "%s\n" \
      "2a8e206f0b171fa5acdce89e5f5798621b227175e5bfa2db6bd92fef63dd962e  /data/JmdictFurigana.json" \
      "ad210aaddf0115509723307d99d02429318e639222549e9bc452050b6ce88db7  /data/JmnedictFurigana.json" \
      "e753440fd7583dfce38c67f5d2dbdf456422adf1fbcffa3eb471ec3538d13bb0  /data/JmdictKanaExpressions.json" \
      "638718c4c63625ab300de4c92c67925d54c0e9e3830009eaa992f29819d59c43  /unidic-3.1.0.zip" | sha256sum -c -

FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential mecab libmecab-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV DATA_DIR=/opt/qzl/data \
    UV_LINK_MODE=copy \
    UV_SYSTEM_PYTHON=1
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements.txt
COPY --from=downloader /unidic-3.1.0.zip /tmp/unidic-3.1.0.zip
COPY scripts scripts
RUN python scripts/install_unidic.py
COPY pyproject.toml .
COPY src src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install .

FROM python:3.13-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmecab2 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local /usr/local
RUN adduser --system --group qzl
# --chown avoids re-copying the data files in a follow-up `chown -R` layer.
COPY --chown=qzl:qzl --from=downloader /data /opt/qzl/data
WORKDIR /app
RUN mkdir -p /app/data && chown qzl:qzl /app/data
USER qzl
ENV DATA_DIR=/opt/qzl/data \
    JMDICT_FURIGANA_CSV=/opt/qzl/data/JmdictFurigana.json \
    JMDICT_FURIGANA_NAMES_CSV=/opt/qzl/data/JmnedictFurigana.json \
    JMDICT_KANA_EXPRESSIONS_JSON=/opt/qzl/data/JmdictKanaExpressions.json
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
