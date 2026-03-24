import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
try:
    client = genai.Client() # Picks up GEMINI_API_KEY or GOOGLE_API_KEY automatically
    models = client.models.list()
    found = False
    for m in models:
        if "embed" in m.name.lower():
            print("Found embedding model:", m.name)
            found = True
    if not found:
        print("No embedding models found for this API key.")
except Exception as e:
    print("Error:", str(e))
