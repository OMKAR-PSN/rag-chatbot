import os
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from app.rag.ingestion import CHROMA_DB_DIR, get_embeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

TARGET_PORTALS = [
    {
        "filename": "pm_kisan_samman_nidhi.txt",
        "url": "https://pmkisan.gov.in/",
        "selector": "body" 
    },
    {
        "filename": "ayushman_bharat_pradhan_mantri_jan_arogya_yojana.txt",
        "url": "https://nha.gov.in/PM-JAY",
        "selector": "body"
    }
]

def get_file_hash(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return hashlib.md5(f.read().encode('utf-8')).hexdigest()

def wipe_and_reingest(filepath):
    print(f"Triggering Vector Re-Ingestion exclusively for {filepath}...")
    
    embeddings = get_embeddings()
    vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    
    try:
        # 1. Delete old chunks for this specific document using metadata filtering
        vectorstore.delete(where={"source": filepath})
        print(f"Deleted old vector chunks for {filepath}")
    except Exception as e:
        print(f"No existing chunks found to delete or error: {e}")
        
    # 2. Load the newly scraped document
    loader = TextLoader(filepath, encoding='utf-8')
    docs = loader.load()
    
    # 3. Split it
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(docs)
    
    # 4. Insert updated chunks
    vectorstore.add_documents(chunks)
    print(f"Successfully re-ingested {len(chunks)} updated chunks into ChromaDB.")

def run_scraper():
    print("Starting Automated Government Portal Scraper (Cron Mode)...")
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    for portal in TARGET_PORTALS:
        filename = portal["filename"]
        url = portal["url"]
        print(f"\n[Scraping] {url}")
        
        try:
            # Mask as standard browser to bypass basic bot protection
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Failed HTTP {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            element = soup.select_one(portal.get('selector', 'body')) or soup
            
            # Clean up JS, CSS, and navigation headers
            for tag in element(["script", "style", "nav", "footer"]):
                tag.extract()
                
            text_content = element.get_text(separator='\n\n', strip=True)
            
            # Compare hashes against local filesystem
            filepath = os.path.abspath(os.path.join(DATA_DIR, filename))
            new_hash = hashlib.md5(text_content.encode('utf-8')).hexdigest()
            old_hash = get_file_hash(filepath)
            
            if new_hash != old_hash:
                print(f"Changes detected on {url}! Processing updates...")
                
                # Overwrite local .txt file
                scheme_name = filename.replace('.txt', '').replace('_', ' ').title()
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# SCHEME NAME: {scheme_name}\n\n")
                    f.write(text_content)
                
                # Execute targeted vector replacement
                wipe_and_reingest(filepath)
                
            else:
                print(f"Data is unchanged since last crawl. Skipping {filename}.")
                
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            
        time.sleep(3) # Politeness delay
        
    print("\nAutomated Web Crawl completed.")

if __name__ == "__main__":
    run_scraper()
