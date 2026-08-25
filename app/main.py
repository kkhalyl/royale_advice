"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import players, cards
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Clash Royale Advice API",
    description="Get gameplay and deck improvement advice for Clash Royale players",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(players.router)
app.include_router(cards.router)


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
