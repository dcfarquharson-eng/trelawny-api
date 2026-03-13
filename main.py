"""
TrelawnyTown API — Standalone FastAPI backend.
Handles: waitlist join, login, change password.
Separate from TheMagneticMind backend entirely.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from db import init_db

app = FastAPI(title="TrelawnyTown API", version="1.0.0")

# Allow requests from the GitHub Pages site
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://trelawnytown.com",
        "https://www.trelawnytown.com",
        "http://localhost:5500",   # local dev live-server
        "http://127.0.0.1:5500",
        "http://localhost:8000",   # python http.server
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(router, prefix="/api/trelawny")

@app.get("/")
def health():
    return {"status": "TrelawnyTown API is live"}
