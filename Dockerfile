FROM python:3.11-slim

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the current directory contents into the container
COPY --chown=user . $HOME/app

# Install dependencies from backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Switch to backend directory so Python module paths resolve correctly
WORKDIR $HOME/app/backend

# Set LLM_PROVIDER so we use local HuggingFace embeddings at build time (no API key needed)
ENV LLM_PROVIDER=groq

# Build the ChromaDB vector database from the text files in data/
# The || echo ensures a build failure here doesn't abort the whole build
RUN python -c "from app.rag.ingestion import ingest_all; ingest_all()" || echo "Ingestion failed — will retry on first request"

# Expose the port Hugging Face expects
ENV PORT=7860
EXPOSE 7860

# Run the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]

