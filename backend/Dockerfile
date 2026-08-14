FROM python:3.13-slim

WORKDIR /app

# Unbuffered stdout/stderr so uvicorn's logs reach `docker compose logs` as
# they happen rather than sitting in a pipe buffer; no .pyc files since the
# source layer is immutable once built.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# NOTE: this image deliberately does NOT install torch/transformers or bake
# the facebook/mms-tts-ben weights. Voice is stalled (the mic button is
# disabled client-side, and app.main's lifespan no longer calls
# init_tts_model()), so those packages are absent from requirements.txt —
# see the module docstring in app/tools/voice.py. Re-add them there, and
# restore a model-prefetch layer here, before re-enabling voice.

COPY . .

RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
