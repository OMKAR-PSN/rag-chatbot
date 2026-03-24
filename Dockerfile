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

# Copy the current directory contents into the container at $HOME/app setting the owner to the user
COPY --chown=user . $HOME/app

# Install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose the port Hugging Face expects
ENV PORT=7860
EXPOSE 7860

# Rebuild the ChromaDB index during the Docker build so it's ready instantly
# We use a quiet python script to trigger the ingestion
RUN python -c "import os; from backend.app.rag.ingestion import ingest_all; ingest_all()" || echo "Ingestion skipped or failed, will retry on startup"

# Run the FastAPI server from the backend folder
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
