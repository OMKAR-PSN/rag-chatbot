import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
try:
    client = genai.Client()
    models = client.models.list()
    print("Found these models:")
    for m in models:
        print(m.name)
except Exception as e:
    print("Error:", repr(e))
