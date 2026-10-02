# fasttext-predict ships prebuilt wheels (unlike fasttext), so no compiler toolchain is needed.
FROM python:3.13-slim AS builder

# Pre-download the model into the HF cache in its own layer, before the
# dependency install, so requirements.txt churn does not re-download it.
RUN pip install --no-cache-dir huggingface_hub \
    && python -c \
    "from huggingface_hub import hf_hub_download; hf_hub_download('HPLT/OpenLID-v3', 'openlid-v3.bin')"

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY --from=builder /root/.cache/huggingface /root/.cache/huggingface

WORKDIR /app

COPY src ./src

EXPOSE 8000

LABEL org.opencontainers.image.title="qzl-language-detection" \
      org.opencontainers.image.description="Language detection service (fastText / OpenLID-v3)"
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/v1/health').read().find(b'\"ready\":true')>=0 else 1)"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
