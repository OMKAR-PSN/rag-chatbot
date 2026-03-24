import os
from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")

def get_embeddings():
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    # If Groq is used, use fast local embeddings to 100% avoid rate limits
    if provider == "groq":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
    if provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        
    return OpenAIEmbeddings()

def load_documents():
    """Load all PDFs from the data directory."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logger.warning(f"Created data directory at {DATA_DIR}. Please add PDFs here.")
        return []
    
    loader = PyPDFDirectoryLoader(DATA_DIR)
    docs = loader.load()
    
    # Also load txt files if any
    txt_loader = DirectoryLoader(DATA_DIR, glob="**/*.txt", loader_cls=TextLoader)
    txt_docs = txt_loader.load()
    
    return docs + txt_docs

def process_and_store_documents():
    """Chunk documents and store in ChromaDB."""
    documents = load_documents()
    if not documents:
        print("No documents found to ingest.")
        return False
        
    print(f"Loaded {len(documents)} documents. Splitting text...")
    
    # Splitter optimized for policy documents (larger chunks, more overlap)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")
    
    embeddings = get_embeddings()
    
    print("Storing in ChromaDB in batches to respect API rate limits...")
    vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    
    batch_size = 10
    import time
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        print(f"Ingesting batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}...")
        try:
            vectorstore.add_documents(batch)
        except Exception as e:
            print(f"Rate limit hit. Waiting 30 seconds... Error: {e}")
            time.sleep(30)
            vectorstore.add_documents(batch)
        time.sleep(4) # Respect the 15 RPM free tier limit
        
    try:
        vectorstore.persist()
    except:
        pass
    print("Ingestion complete.")
    return True

def ingest_all():
    """Entry point callable from Dockerfile RUN step and FastAPI lifespan."""
    result = process_and_store_documents()
    if result:
        logger.info("✅ Ingestion complete — ChromaDB is ready.")
    else:
        logger.warning("⚠️ Ingestion produced no documents. Check the data/ folder.")
    return result


if __name__ == "__main__":
    process_and_store_documents()
