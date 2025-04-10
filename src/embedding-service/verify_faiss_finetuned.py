import faiss
import numpy as np
import psycopg2
import re
import ast
from config import DB_CONFIG

# Connect to PostgreSQL
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Prompt user for part of an existing message
search_text = input("Enter part of an existing message: ")

# Search for the message ID using regex
cur.execute("SELECT message_id, text FROM messages")
rows = cur.fetchall()

# Find the matching message
matching_message = None
for message_id, message_text in rows:
    if re.search(re.escape(search_text), message_text, re.IGNORECASE):
        matching_message = (message_id, message_text)
        break

if not matching_message:
    print("No matching message found.")
    exit(1)

message_id, message_text = matching_message
print(f"Found message ID: {message_id}")

# Load FAISS HNSW index
index = faiss.read_index("faiss_index_finetuned.bin")

# Retrieve the corresponding embedding from the database
cur.execute("SELECT vector FROM embeddings WHERE message_id = %s", (message_id,))
vector_row = cur.fetchone()

if not vector_row:
    print("No embedding found for this message.")
    exit(1)

# Convert stored vector to a NumPy array
vector = np.array(ast.literal_eval(vector_row[0]), dtype=np.float32).reshape(1, -1)

# Ensure normalization (important for cosine similarity)
faiss.normalize_L2(vector)

# Search FAISS index
k = 10  # Retrieve 10 candidates first
D, I = index.search(vector, k)

# Filter out the input message itself and rank by score
filtered_results = []
for idx, score in zip(I[0], D[0]):
    if idx == -1:
        continue  # Skip invalid indices
    
    cur.execute("SELECT message_id FROM embeddings LIMIT 1 OFFSET %s", (int(idx),))
    embedding_result = cur.fetchone()
    
    if embedding_result and embedding_result[0] != message_id:
        filtered_results.append((embedding_result[0], score))

# Sort results by descending similarity score
filtered_results = sorted(filtered_results, key=lambda x: x[1], reverse=True)[:3]

print("\nTop 3 closest messages:")
for retrieved_message_id, score in filtered_results:
    cur.execute("SELECT message_id, text FROM messages WHERE message_id = %s", (retrieved_message_id,))
    result = cur.fetchone()
    if result:
        print(f"\nMessage ID: {result[0]}")
        print(f"Message: {result[1]}")
        print(f"Score: {score:.4f}")

# Close DB connection
cur.close()
conn.close()
