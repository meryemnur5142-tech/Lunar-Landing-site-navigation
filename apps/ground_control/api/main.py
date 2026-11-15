"""
LUNA-AI Ground Control API

Start the server:
    # from repo root
    pip install fastapi uvicorn
    uvicorn apps.ground_control.api.main:app --reload

    # or via the helper script
    python run_server.py

Interactive docs after start:
    http://localhost:8000/docs      (Swagger UI)
    http://localhost:8000/redoc     (ReDoc)
"""

from __future__ import annotations

import sys
import os

# Allow running from repo root without install
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
)))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.health import router as health_router
from .routes.candidates import router as candidates_router
from .routes.evaluate import router as evaluate_router
from .routes.mission import router as mission_router
from .routes.efficiency import router as efficiency_router

app = FastAPI(
    title="LUNA-AI Ground Control API",
    description=(
        "REST API for the LUNA-AI lunar landing site evaluation system. "
        "Provides hard-constraint filtering, multi-criteria scoring, and "
        "mission status endpoints for the ground control UI."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow the UI (served separately) to call this API in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # restrict to actual UI origin in production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(candidates_router)
app.include_router(evaluate_router)
app.include_router(mission_router)
app.include_router(efficiency_router)
