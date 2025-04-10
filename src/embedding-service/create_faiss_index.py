import faiss
import numpy as np
import psycopg2
from config import DB_CONFIG

# Connect to PostgreSQL
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Fetch all embeddings from the database
cur.execute("SELECT vector FROM embeddings ORDER BY message_id")
rows = cur.fetchall()

if not rows:
    print("No embeddings found in the database.")
    exit(1)

# Convert stored vectors to NumPy array
embeddings = np.array([np.array(eval(row[0]), dtype=np.float32) for row in rows])

# Ensure embeddings are normalized (important for cosine similarity)
faiss.normalize_L2(embeddings)

# Get vector dimension
dim = embeddings.shape[1]

# Create HNSW index with INNER_PRODUCT for cosine similarity
index = faiss.IndexHNSWFlat(dim, 32, faiss.METRIC_INNER_PRODUCT)
index.hnsw.efConstruction = 200  # More accurate index
index.hnsw.efSearch = 100  # Better recall during search

# Add embeddings to FAISS index
index.add(embeddings)

# Save FAISS index
faiss.write_index(index, "faiss_index_finetuned.bin")

print("FAISS HNSW index created and saved as faiss_index_finetuned.bin")

# Close DB connection
cur.close()
conn.close()
