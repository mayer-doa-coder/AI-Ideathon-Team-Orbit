from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.agents.checkpointer import init_checkpointer
from app.api.routes import alerts, auth, bdapps, chat, consultancy, farms, market, monitor, payment, rag, trace
from app.core.config import settings
from app.scheduler import start_scheduler, stop_scheduler
from app.tools.voice import AUDIO_OUTPUT_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_checkpointer()
    # Voice is currently stalled (mic button disabled client-side) and
    # torch/transformers aren't installed right now (see tools/voice.py) —
    # loading the TTS model here was blocking startup for a feature nobody
    # can reach. Call init_tts_model() again once voice is re-enabled.
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Green Leaf AI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(rag.router)
app.include_router(chat.router)
app.include_router(farms.router)
app.include_router(monitor.router)
app.include_router(alerts.router)
app.include_router(trace.router)
app.include_router(bdapps.router)
app.include_router(market.router)
app.include_router(payment.router)
app.include_router(consultancy.router)

# Serves synthesize_speech's .wav output so the frontend can actually play
# voice_output.audio_path — StaticFiles requires the directory to exist at
# mount time, so create it up front rather than waiting for the first TTS
# call (see app.tools.voice.synthesize_speech).
AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/generated_audio", StaticFiles(directory=str(AUDIO_OUTPUT_DIR)), name="generated_audio")


@app.get("/")
def root():
    return {"status": "ok", "service": "Green Leaf AI API"}
