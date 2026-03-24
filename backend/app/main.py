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
    logger.info("🔥 Warming up RAG components...")
    try:
        # Initialize DB Pool
        db_url = os.getenv("DATABASE_URL")
        # Ensure we don't connect to serverless pooler incorrectly on Windows
        if db_url and "pooler" in db_url:
            db_url = db_url.replace("?sslmode=require&channel_binding=require", "?sslmode=require")
        
        if db_url:
            app.state.pool = await asyncpg.create_pool(db_url, min_size=1, max_size=10)
            logger.info("✅ Asyncpg connection pool ready.")
        else:
            logger.error("⚠️ DATABASE_URL not set in .env! Offline/Local DB not fully hooked to asyncpg here.")
            app.state.pool = None
            
        from app.rag.retrieval import get_vectorstore, get_llm
        # get_vectorstore()   # loads ChromaDB index into memory
        # get_llm()           # initialises LLM client
        logger.info("✅ RAG components bypassed on startup to prevent cloud timeout — will load on first request.")
    except FileNotFoundError:
        logger.warning(
            "⚠️  ChromaDB not found — POST /api/ingest to build the index."
        )
    except Exception as e:
        logger.error("Warmup error (non-fatal): %s", e)
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
