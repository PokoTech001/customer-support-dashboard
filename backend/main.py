import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import analyze, calls, recordings
from services.gemini_client import gemini_client
from services.tts_client import tts_client

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await tts_client.ensure_authenticated()
    yield
    await tts_client.logout()
    await tts_client.close()
    await gemini_client.close()


app = FastAPI(title="Customer Support Dashboard API", lifespan=lifespan)

# CORS — allow all origins in dev; restrict to FRONTEND_ORIGIN in production
origins = (
    ["*"]
    if settings.environment.lower() == "development"
    else [settings.frontend_origin]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calls.router)
app.include_router(recordings.router)
app.include_router(analyze.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
