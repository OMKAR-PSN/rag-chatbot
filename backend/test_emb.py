from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

emb = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key="AIzaSyCBu3u3sj2F7ciHCvkCnRg1B6Oijj50bxw")
print("model:", emb.model)
print("dimensions:", len(emb.embed_query("test")))
