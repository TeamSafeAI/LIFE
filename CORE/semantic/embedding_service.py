"""
Embedding Service - Standalone HTTP server for semantic search.

Run this before using semantic memory for full search capability.
Without it, semantic_store and semantic_recent still work, 
but semantic_search falls back to recency-based results.

Usage:
    pip install sentence-transformers fastapi uvicorn
    python embedding_service.py

Runs on http://127.0.0.1:5050
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import uvicorn
import os

# Cache setup
cache_dir = os.path.expanduser("~/.cache/huggingface")
os.environ["TRANSFORMERS_CACHE"] = cache_dir
os.environ["HF_HOME"] = cache_dir

app = FastAPI()
model = None

class EmbedRequest(BaseModel):
    text: str

@app.on_event("startup")
async def load_model():
    global model
    print("Loading sentence transformer (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=cache_dir)
    print("Model ready")

@app.get("/health")
async def health():
    return {"status": "ready" if model else "loading", "model": "all-MiniLM-L6-v2"}

@app.post("/encode")
async def encode(request: EmbedRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        embedding = model.encode(request.text)
        return {"embedding": embedding.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5050, log_level="info")
