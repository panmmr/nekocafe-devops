# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /build
COPY requirements.lock .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.lock

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    mkdir -p /data

COPY --from=builder /root/.local /home/appuser/.local

WORKDIR /app
COPY src/ ./src/

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV RESERVATION_DB_PATH=/data/reservation.db

RUN chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
