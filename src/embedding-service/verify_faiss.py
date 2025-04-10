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
print(f"✅ Found message ID: {message_id}")

# Load FAISS index
index = faiss.read_index("faiss_index.bin")

print(f"🔍 FAISS index type: {type(index)}")
print(f"🔍 FAISS metric type: {index.metric_type}")  # Should be METRIC_INNER_PRODUCT for cosine similarity


# Retrieve the corresponding embedding from the database
cur.execute("SELECT vector FROM embeddings WHERE message_id = %s", (message_id,))
vector_row = cur.fetchone()

if not vector_row:
    print("❌ No embedding found for this message.")
    exit(1)

# Debugging: Print raw vector details
print(f"🔍 Raw vector type: {type(vector_row[0])}")
print(f"🔍 Raw vector content (first 10 values): {str(vector_row[0])[:100]}...")  # Print first 100 chars

# Convert stored vector to a NumPy array
if isinstance(vector_row[0], str):  # If stored as TEXT, convert to list
    vector = np.array(ast.literal_eval(vector_row[0]), dtype=np.float32).reshape(1, -1)
elif isinstance(vector_row[0], list):  # If stored as an actual list
    vector = np.array(vector_row[0], dtype=np.float32).reshape(1, -1)
else:
    print("❌ Unexpected vector format!")
    exit(1)

# Search FAISS index
D, I = index.search(vector, k=5)  # Find 5 nearest neighbors

# Debug: Verify FAISS index-to-message_id mapping
print("\nFAISS index-to-message_id mapping:")

for idx in I[0]:
    if idx == -1:
        continue  # Skip invalid indices

    cur.execute("SELECT message_id FROM embeddings LIMIT 1 OFFSET %s", (int(idx),))
    embedding_result = cur.fetchone()

    if embedding_result:
        retrieved_message_id = embedding_result[0]
        print(f"Index: {idx} → Message ID: {retrieved_message_id}")

print(f"\nFAISS search results (distances & indices):")
for dist, idx in zip(D[0], I[0]):
    print(f"Index: {idx}, Distance: {dist}")

print("\n🔎 Verifying FAISS index order:")

for idx, distance in zip(I[0], D[0]):
    if idx == -1:
        continue  # Skip invalid indices

    cur.execute("SELECT message_id, text FROM messages WHERE message_id = (SELECT message_id FROM embeddings LIMIT 1 OFFSET %s)", (int(idx),))
    result = cur.fetchone()

    if result:
        retrieved_message_id, retrieved_text = result
        print(f"FAISS Index: {idx} | Distance: {distance}")
        print(f"📌 Message ID: {retrieved_message_id}")
        print(f"📜 Message: {retrieved_text[:200]}...\n")  # Print first 200 chars for readability    

print("\n🔎 Top 5 closest messages:")
for idx in I[0]:
    if idx == -1:
        continue  # Skip invalid indices

    # Retrieve the actual message_id using FAISS' stored index mapping
    cur.execute("SELECT message_id FROM embeddings LIMIT 1 OFFSET %s", (int(idx),))
    embedding_result = cur.fetchone()
    
    if embedding_result:
        retrieved_message_id = embedding_result[0]
        cur.execute("SELECT message_id, text FROM messages WHERE message_id = %s", (retrieved_message_id,))
        result = cur.fetchone()
        if result:
            print(f"\n📌 Message ID: {result[0]}\n📜 Message: {result[1]}\n")

# Close DB connection
cur.close()
conn.close()
