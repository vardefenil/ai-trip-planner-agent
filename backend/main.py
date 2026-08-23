"""
AI Travel Planning Agent — FastAPI Backend
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

_backend_env = Path(__file__).resolve().parent / ".env"
if _backend_env.exists():
    load_dotenv(_backend_env)
else:
    load_dotenv(find_dotenv())
load_dotenv()


from routers import trip, chat

app = FastAPI(
    title="AI Travel Planner Agent",
    description="An AI-powered travel planning agent that creates personalised India trip packages",
    version="1.0.0",
)

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip.router, prefix="/api", tags=["Trip Planning"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])


@app.get("/")
async def root():
    return {
        "status": "running",
        "message": "AI Travel Planner Agent API is live 🚀",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
