import faiss
import numpy as np
import psycopg2
import pickle
from config import DB_CONFIG

# Connect to PostgreSQL
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Step 1: Fetch parent message embeddings (FAISS should use only parent threads)
cursor.execute("""
    SELECT m.message_id, e.vector
    FROM messages m
    JOIN embeddings e ON m.message_id = e.message_id
    WHERE m.parent_id IS NULL
    ORDER BY m.created
""")
rows = cursor.fetchall()

if not rows:
    print("❌ No parent message embeddings found.")
    exit(1)

# Step 2: Extract message_ids and vectors
message_ids = [row[0] for row in rows]
embeddings = np.array([np.array(eval(row[1]), dtype=np.float32) for row in rows])

# Step 3: Normalize vectors (for cosine similarity)
faiss.normalize_L2(embeddings)

# Step 4: Build FAISS HNSW index with inner product (cosine similarity)
dim = embeddings.shape[1]
index = faiss.IndexHNSWFlat(dim, 32, faiss.METRIC_INNER_PRODUCT)
index.hnsw.efConstruction = 200
index.hnsw.efSearch = 100
index.add(embeddings)

# Step 5: Save FAISS index
faiss.write_index(index, "faiss_index_finetuned.bin")
print(f"✅ FAISS index saved with {len(message_ids)} parent messages.")

# Step 6: Save ID map: index position → message_id
id_map = {i: msg_id for i, msg_id in enumerate(message_ids)}
with open("faiss_id_map.pkl", "wb") as f:
    pickle.dump(id_map, f)
print("✅ FAISS ID map saved to faiss_id_map.pkl")

# Step 7: Save message_ids to .ids file (optional but useful)
with open("faiss_index_finetuned.ids", "w") as f:
    for msg_id in message_ids:
        f.write(msg_id + "\n")
print("✅ Message IDs saved to faiss_index_finetuned.ids")

# Clean up
cursor.close()
conn.close()
