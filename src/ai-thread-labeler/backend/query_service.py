import faiss
import numpy as np
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend import models
import os
import pickle

FAISS_INDEX_PATH = "embedding-service/faiss_index_finetuned.bin"
EMBEDDING_DIM = 768  # Change if your embedding size differs

class QueryService:
    def __init__(self):
        self.index = None
        self.id_map = []
        self.load_faiss_index()

    def load_faiss_index(self):
        if not os.path.exists(FAISS_INDEX_PATH):
            raise RuntimeError(f"FAISS index not found at {FAISS_INDEX_PATH}")
        self.index = faiss.read_index(FAISS_INDEX_PATH)

        # Load ID mapping if using IndexIDMap or similar
        with open(FAISS_INDEX_PATH + ".ids", "rb") as f:
            self.id_map = pickle.load(f)

    def get_db(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def search_similar_threads(self, query_embedding: np.ndarray, top_k: int = 5):
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        distances, indices = self.index.search(query_embedding, top_k)
        matched_ids = [self.id_map[i] for i in indices[0] if i != -1]
        return matched_ids
