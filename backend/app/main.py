from fastapi import FastAPI, Request
from pydantic import BaseModel
import json
from app.vector_store import VectorStore
from app.data_loader import load_and_chunk_documents
from app.gemini_qa import GeminiAnswerer

app = FastAPI()

# Load or build chunks
try:
    with open("data/processed_chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
except:
    chunks = load_and_chunk_documents()

# Setup search and Gemini
vs = VectorStore()
vs.build_index(chunks)
gemini = GeminiAnswerer()

class QueryRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return {"message": "Legal Chatbot backend is running!"}

@app.post("/ask")
async def ask_legal_bot(req: QueryRequest):
    top_chunks = vs.query(req.question)
    answer = gemini.format_answer(top_chunks, req.question)
    return {"response": answer}

