import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorStore:
    def __init__(self, embedding_model="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(embedding_model)
        self.index = None
        self.texts = []

    def build_index(self, chunks):
        self.texts = [chunk['text'] for chunk in chunks]
        embeddings = self.model.encode(self.texts, show_progress_bar=True)
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(np.array(embeddings).astype('float32'))

    def query(self, user_query, top_k=3):
        query_vec = self.model.encode([user_query]).astype('float32')
        D, I = self.index.search(query_vec, top_k)
        return [self.texts[i] for i in I[0]]