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

# Extract message_ids and vectors
message_ids = [row[0] for row in rows]
# Convert to NumPy array
embeddings = np.array([np.array(eval(row[0]), dtype=np.float32) for row in rows])

# Verify normalization
print(f"Before normalization: Norm of first embedding: {np.linalg.norm(embeddings[0])}")

# Normalize vectors for cosine similarity
faiss.normalize_L2(embeddings)

# Verify normalization again
print(f"After normalization: Norm of first embedding: {np.linalg.norm(embeddings[0])}")

# Get vector dimension
dim = embeddings.shape[1]

# Create HNSW index with INNER_PRODUCT for cosine similarity
index = faiss.IndexHNSWFlat(dim, 32, faiss.METRIC_INNER_PRODUCT)
index.hnsw.efConstruction = 200  # More accurate index
index.hnsw.efSearch = 100  # Better recall during search

# Add embeddings to FAISS index
index.add(embeddings)

# Save index
faiss.write_index(index, "faiss_index_finetuned.bin")

with open("faiss_index_finetuned.ids", "w") as f:
    for mid in message_ids:
        f.write(mid + "\n")

print("FAISS HNSW index created and saved as faiss_index_finetuned.bin")
print("Message IDs saved to faiss_index_finetuned.ids")

# Close DB connection
cur.close()
conn.close()
