"""
AI Travel Planning Agent — FastAPI Backend
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_backend_env = Path(__file__).resolve().parent / ".env"
if _backend_env.exists():
    load_dotenv(_backend_env)
else:
    load_dotenv(find_dotenv())
load_dotenv()

import database
from routers import trip, chat, sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database (PostgreSQL / SQLite fallback)
    await database.init_db()
    yield
    # Shutdown


app = FastAPI(
    title="AI Travel Planner Agent",
    description="An AI-powered travel planning agent that creates personalised India trip packages",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow frontend to call backend (Vercel, Localhost, and any custom domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip.router, prefix="/api", tags=["Trip Planning"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])


@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {
        "status": "running",
        "message": "AI Travel Planner Agent API is live",
        "docs": "/docs",
    }


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "healthy"}

