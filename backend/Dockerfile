FROM python:3.13-slim

WORKDIR /app

# CPU-only torch — the default PyPI wheel pulls in the full CUDA toolchain
# (several GB of nvidia-*-cu12 packages) that's never used, since the
# MMS-TTS voice model only ever runs on CPU (see app/tools/voice.py).
# requirements.txt lists plain "torch" with no version pin, so the later
# `pip install -r requirements.txt` sees it already satisfied and leaves
# this build alone.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bakes the MMS-TTS Bengali weights into the image at build time — before
# COPY . . so this layer only invalidates when requirements.txt itself
# changes, not on every source edit. Without this, app.tools.voice's
# init_tts_model() (called from app.main's lifespan on every container
# start) would need live Hugging Face Hub access and add real startup
# latency on every restart.
RUN python -c "from transformers import AutoTokenizer, VitsModel; \
VitsModel.from_pretrained('facebook/mms-tts-ben'); \
AutoTokenizer.from_pretrained('facebook/mms-tts-ben')"

COPY . .

RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
