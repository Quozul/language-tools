# Alpine was tried first (docs 14.6 decision gate): mecab/mecab-dev are not
# packaged in Alpine repositories, so MeCab cannot be built on musl.
# Per the docs, correctness wins over image size: using slim (Debian/glibc).

FROM python:3.13-slim AS builder
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential mecab libmecab-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV DATA_DIR=/opt/qzl/data
# Assets are downloaded by a stdlib-only script, so this layer is independent
# of requirements.txt churn.
COPY scripts scripts
RUN python scripts/download_assets.py /opt/qzl/data
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Separate layer: re-downloads unidic only when this command changes.
RUN python -m unidic download
COPY pyproject.toml .
COPY src src
RUN pip install --no-cache-dir . pytest httpx
# Test-only layering: run tests with: docker build --target builder
COPY tests tests
COPY data/gold data/gold

FROM python:3.13-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmecab2 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local /usr/local
COPY --from=builder /opt/qzl/data /opt/qzl/data
WORKDIR /app
RUN adduser --system --group qzl \
    && mkdir -p /app/data && chown -R qzl:qzl /app /opt/qzl
USER qzl
ENV DATA_DIR=/opt/qzl/data \
    JMDICT_FURIGANA_CSV=/opt/qzl/data/JmdictFurigana.json \
    JMDICT_FURIGANA_NAMES_CSV=/opt/qzl/data/JmnedictFurigana.json
EXPOSE 8000
LABEL org.opencontainers.image.title="qzl-transliterate" \
      org.opencontainers.image.description="Text annotation service (furigana + romaji), PoC: Japanese"
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/v1/health').read().find(b'\"ready\":true')>=0 else 1)"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
