from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.api.registration import router as registration_router
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


# ── Startup warmup ────────────────────────────────────────────────────────────
# Pre-loads ChromaDB and LLM so the FIRST user request is fast, not the server.

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔥 Starting PRATINIDHI RAG Backend...")
    try:
        # Initialize DB Pool
        db_url = os.getenv("DATABASE_URL")
        if db_url and "pooler" in db_url:
            db_url = db_url.replace("?sslmode=require&channel_binding=require", "?sslmode=require")
        
        if db_url:
            app.state.pool = await asyncpg.create_pool(db_url, min_size=1, max_size=10)
            logger.info("✅ Asyncpg connection pool ready.")
        else:
            logger.warning("⚠️ DATABASE_URL not set — DB features will be unavailable.")
            app.state.pool = None
            
        # Auto-build ChromaDB if it doesn't exist (first cloud boot)
        from app.rag.ingestion import CHROMA_DB_DIR, ingest_all
        if not os.path.exists(CHROMA_DB_DIR):
            logger.info("🔨 ChromaDB not found — building from data/ files now...")
            import threading
            t = threading.Thread(target=ingest_all, daemon=True)
            t.start()
            logger.info("✅ ChromaDB build started in background thread.")
        else:
            logger.info("✅ ChromaDB found on disk — ready to serve queries.")

    except Exception as e:
        logger.error("Startup error (non-fatal): %s", e)
    yield
    
    # Shutdown DB Pool
    if hasattr(app.state, "pool") and app.state.pool:
        await app.state.pool.close()
        logger.info("✅ Asyncpg connection pool closed.")
    logger.info("RAG backend shutting down.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="India Innovates RAG API",
    description="Sakhi — AI assistant for Indian Government Schemes",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5000",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8000",
        "http://10.0.2.2",
        "http://10.0.2.2:8000",   # Android emulator → host machine
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(registration_router, prefix="/api")


@app.get("/")
def health_check():
    return {"status": "ok", "message": "India Innovates RAG Backend is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
