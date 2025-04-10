import faiss
import numpy as np
import psycopg2
from config import DB_CONFIG

# Connect to PostgreSQL
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Fetch all embeddings from the database
cur.execute("SELECT message_id, vector FROM embeddings ORDER BY message_id")
rows = cur.fetchall()

if not rows:
    print("No embeddings found in the database.")
    exit(1)

# Convert to NumPy array
embeddings = np.array([np.array(eval(row[1]), dtype=np.float32) for row in rows])

# Normalize embeddings
faiss.normalize_L2(embeddings)

# Verify normalization
print(f"Norm of first embedding after normalization: {np.linalg.norm(embeddings[0])}")  # Should be ≈1.0

# Update normalized embeddings back to PostgreSQL
for (message_id, vector) in zip([row[0] for row in rows], embeddings):
    cur.execute("UPDATE embeddings SET vector = %s WHERE message_id = %s", (vector.tolist(), message_id))

conn.commit()
print("✅ Stored embeddings have been normalized and updated in PostgreSQL.")

# Close DB connection
cur.close()
conn.close()
