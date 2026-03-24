import os
import json
from functools import lru_cache

from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.rag.ingestion import CHROMA_DB_DIR
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# ── Cached singletons — loaded once, reused forever ──────────────────────────

@lru_cache(maxsize=1)
def get_llm():
    """Instantiated once at startup, reused for every request."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "groq":
        from langchain_groq import ChatGroq
        model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        return ChatGroq(model=model, temperature=0.3, max_tokens=512)
    elif provider == "gemini":
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, temperature=0.3)
    
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model, temperature=0.3)


@lru_cache(maxsize=1)
def _get_embeddings_cached():
    """Embeddings client — cached so we never re-instantiate per request."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    # If Groq is used, use fast local embeddings to 100% avoid rate limits
    if provider == "groq":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
    if provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings()


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    """
    ChromaDB loaded once from disk at startup.
    Eliminates the 1-2s cold-start penalty on the first request.
    """
    logger.info("Loading ChromaDB vectorstore...")
    if not os.path.exists(CHROMA_DB_DIR):
        raise FileNotFoundError(
            f"ChromaDB not found at '{CHROMA_DB_DIR}'. POST /api/ingest first."
        )
    vs = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=_get_embeddings_cached(),
    )
    logger.info("ChromaDB loaded and cached ✓")
    return vs


@lru_cache(maxsize=1)
def get_retriever():
    """k=3 — 3 chunks is enough for scheme Q&A and is faster than k=4."""
    return get_vectorstore().as_retriever(search_kwargs={"k": 3})


# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are Sakhi, a friendly expert on Indian Government schemes and policies. "
    "Your audience is the general public. Use Markdown for formatting.\n\n"
    "Rules:\n"
    "1. Answer ONLY from the provided context.\n"
    "2. Use simple language — avoid jargon.\n"
    "3. Use bullet points for eligibility and application steps.\n"
    "4. If the answer isn't in context, say 'I don't have information on that scheme'.\n"
    "5. Always name the specific scheme.\n\n"
    "Context:\n{context}\n\n"
    "User Question: {question}"
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _contextualize_question(question: str, history: list) -> str:
    """Rephrases question as standalone using last 4 turns of history."""
    if not history:
        return question

    history_str = "".join(
        f"{h['role'].capitalize()}: {h['content']}\n"
        for h in history[-4:]
    )
    prompt = (
        "Rephrase the latest question as a self-contained standalone question "
        "using the conversation history. If no rephrasing is needed, return it exactly.\n\n"
        f"History:\n{history_str}\n"
        f"Latest Question: {question}\n\n"
        "Standalone Question:"
    )
    response = get_llm().invoke([HumanMessage(content=prompt)])
    return response.content.strip()


# ── Main sync streaming generator ─────────────────────────────────────────────

def query_rag_stream(
    question: str,
    language: str = "English",
    history: list = None,
    profile: dict = None,
):
    """
    Sync generator — yields SSE strings.
    FastAPI's StreamingResponse handles sync generators correctly.
    Keeping it sync avoids thread-safety issues with ChromaDB + LangChain.
    """
    # ── Retriever init (instant after warmup) ────────────────────────────────
    try:
        retriever = get_retriever()
    except FileNotFoundError as e:
        logger.error(str(e))
        yield f"data: {json.dumps({'type': 'chunk', 'data': '⚠️ Knowledge base is empty. Please run /api/ingest first.'})}\n\n"
        return

    try:
        llm = get_llm()

        # Contextualize only when there's history
        standalone = (
            _contextualize_question(question, history) if history else question
        )

        # Retrieve top-3 docs
        docs = retriever.invoke(standalone)
        context_text = "\n\n".join(doc.page_content for doc in docs)

        # Emit sources first so Flutter can render them
        sources = list({
            os.path.basename(doc.metadata.get("source", "Unknown"))
            for doc in docs
        })
        yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"

        # Build full prompt
        profile_text = ""
        if profile and any(profile.values()):
            profile_text = (
                "USER PROFILE:\n"
                f"Age: {profile.get('age') or 'Not specified'}\n"
                f"Gender: {profile.get('gender') or 'Not specified'}\n"
                f"Annual Income: {profile.get('income') or 'Not specified'}\n"
                f"Caste/Category: {profile.get('caste') or 'Not specified'}\n"
                f"Location: {profile.get('location') or 'Not specified'}\n\n"
                "ELIGIBILITY CHECK: If the user's profile clearly violates the "
                "scheme's eligibility criteria, politely say so first.\n\n"
            )

        history_text = ""
        if history:
            history_text = "Previous Conversation:\n" + "".join(
                f"{h['role'].capitalize()}: {h['content']}\n"
                for h in history[-4:]
            ) + "\n\n"

        final_prompt = SYSTEM_PROMPT.format(
            context=context_text, question=question
        )
        if profile_text:
            final_prompt = profile_text + final_prompt
        if history_text:
            final_prompt = history_text + final_prompt

        final_prompt += (
            f"\n\nIMPORTANT: Answer in **{language}** using Markdown. "
            "If the context has an official application URL, include at the end: "
            "`[👉 Click Here to Apply](URL)`"
        )

        # Stream tokens — sync generator, works perfectly with StreamingResponse
        for chunk in llm.stream([HumanMessage(content=final_prompt)]):
            if chunk.content:
                yield f"data: {json.dumps({'type': 'chunk', 'data': chunk.content})}\n\n"

    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg or "retryinfo" in error_msg:
            logger.error("Rate limit hit: %s", e)
            yield f"data: {json.dumps({'type': 'chunk', 'data': '⚠️ The AI is currently overloaded with requests (Rate Limit Hit). Please wait 30 seconds and try again.'})}\n\n"
        else:
            logger.error("RAG query error: %s", e, exc_info=True)
            yield f"data: {json.dumps({'type': 'chunk', 'data': 'Sorry, something went wrong. Please try again later.'})}\n\n"
