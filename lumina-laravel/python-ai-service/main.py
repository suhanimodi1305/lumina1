"""
Lumina AI Microservice — FastAPI wrapper
Wraps existing Python AI code (unchanged) and exposes REST endpoints
consumed by the Laravel 12 application.

Start: uvicorn main:app --host 0.0.0.0 --port 8001 --reload
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

# ── Load .env from Django project root so AI keys are available standalone ──
_env_path = Path(__file__).resolve().parents[2] / '.env'
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _key, _, _val = _line.partition('=')
                os.environ.setdefault(_key.strip(), _val.strip())

from fastapi import FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from routers import scan, chat

# ── Bearer token auth ──────────────────────────────────────────
AI_SERVICE_TOKEN = os.getenv("AI_SERVICE_TOKEN", "")
security = HTTPBearer(auto_error=False)


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
    """Validate the Bearer token sent by Laravel."""
    if not AI_SERVICE_TOKEN:
        # No token configured → open (development only)
        return True
    if credentials is None or credentials.credentials != AI_SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Bearer token.",
        )
    return True


# ── App factory ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✨ Lumina AI Service starting up...")
    yield
    print("Lumina AI Service shutting down.")


app = FastAPI(
    title="Lumina AI Service",
    description="Python AI microservice for skin analysis and chat (wraps existing code).",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: only allow requests from Laravel app
ALLOWED_ORIGINS = os.getenv("AI_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Routers ────────────────────────────────────────────────────
app.include_router(scan.router,  prefix="/api/v1/scan",  tags=["scan"])
app.include_router(chat.router,  prefix="/api/v1/chat",  tags=["chat"])


# ── Health check ───────────────────────────────────────────────
@app.get("/api/v1/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "lumina-ai"}
