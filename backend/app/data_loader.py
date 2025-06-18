import os
import json

def chunk_text(text, chunk_size=100, overlap=20):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append({"text": chunk})
    return chunks

def load_and_chunk_documents(folder_path="data/legal_docs"):
    chunks = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                text = f.read()
                chunks.extend(chunk_text(text))
    with open("data/processed_chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    return chunks