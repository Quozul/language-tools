FROM alpine:3.20 AS downloader
ARG MIRROR_URL=https://files.quozul.dev/qzl-mirror
RUN wget -q -O /openlid-v3.bin "$MIRROR_URL/openlid-v3.bin" \
    && printf "%s\n" "01ec5bbf85975c52673c52b3d8585bc4cc0e4eb4636ad5591467bab56b118821  /openlid-v3.bin" | sha256sum -c -

FROM python:3.13-slim AS builder
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY --from=downloader /openlid-v3.bin /opt/qzl/models/openlid-v3.bin
WORKDIR /app
COPY src ./src
ENV MODEL_PATH=/opt/qzl/models/openlid-v3.bin
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
