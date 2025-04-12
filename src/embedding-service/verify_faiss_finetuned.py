import faiss
import numpy as np
import psycopg2
import re
import ast
from config import DB_CONFIG

# Connect to PostgreSQL
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Build mapping: get the list of message IDs in the same order used for index creation.
cur.execute("SELECT message_id FROM embeddings ORDER BY message_id")
all_ids = [row[0] for row in cur.fetchall()]
print(f"Built mapping for {len(all_ids)} embeddings.")

# Prompt user for part of an existing message (for query)
search_text = input("Enter part of an existing message: ")

# Search for the matching message (based on the text column) in the messages table.
cur.execute("SELECT message_id, text FROM messages")
rows = cur.fetchall()
matching_message = None
for message_id, message_text in rows:
    if re.search(re.escape(search_text), message_text, re.IGNORECASE):
        matching_message = (message_id, message_text)
        break

if not matching_message:
    print("No matching message found.")
    exit(1)

query_message_id, query_text = matching_message
print(f"✅ Found message ID: {query_message_id}")

# Retrieve the corresponding embedding from the database
cur.execute("SELECT vector FROM embeddings WHERE message_id = %s", (query_message_id,))
vector_row = cur.fetchone()
if not vector_row:
    print("No embedding found for this message.")
    exit(1)

# Convert stored vector to a NumPy array.
# (The vector is stored as a string; use ast.literal_eval to get the Python list, then make a NumPy array.)
query_vector = np.array(ast.literal_eval(vector_row[0]), dtype=np.float32).reshape(1, -1)

# Ensure normalization for cosine similarity (using inner product metric)
faiss.normalize_L2(query_vector)

# Load the fine-tuned FAISS HNSW index
index = faiss.read_index("faiss_index_finetuned.bin")

# Search FAISS index for top k similar vectors (here we use k=10 initially)
k = 10
distances, indices = index.search(query_vector, k)

# Debug: print raw FAISS search results (indices and distances)
print("\n🔎 FAISS search results (raw indices & distances):")
for idx, d in zip(indices[0], distances[0]):
    print(f"Index: {idx}, Distance: {d}")

# Create filtered results using the mapping.
# For each FAISS index, we use 'all_ids' to get the corresponding message_id.
filtered_results = []
for idx, score in zip(indices[0], distances[0]):
    if idx == -1:
        continue  # Skip invalid indices
    retrieved_message_id = all_ids[int(idx)]
    # Exclude the query message itself
    if retrieved_message_id == query_message_id:
        continue
    filtered_results.append((retrieved_message_id, float(score)))

# For thread-level ranking: group results by thread.
# If a message is a child (has a non-null parent_id), we treat the parent as the thread identifier.
thread_scores = {}  # mapping: thread_id -> list of scores
for matched_id, score in filtered_results:
    cur.execute("SELECT parent_id FROM messages WHERE message_id = %s", (matched_id,))
    result = cur.fetchone()
    # If parent_id exists, use it; otherwise, this message is the thread root.
    thread_id = result[0] if result and result[0] is not None else matched_id
    thread_scores.setdefault(thread_id, []).append(score)

# Compute an aggregated thread score (average of scores)
thread_ranking = []
for thread_id, scores in thread_scores.items():
    agg_score = sum(scores) / len(scores)
    thread_ranking.append((thread_id, agg_score))

# Sort threads by aggregated score in descending order
thread_ranking.sort(key=lambda x: x[1], reverse=True)

# Display the top N threads, including the parent message and all its child messages
TOP_N = 3
print(f"\n📊 Top {TOP_N} Threads (by aggregated score):\n")
for thread_id, agg_score in thread_ranking[:TOP_N]:
    print("=" * 80)
    print(f"Thread Root (Parent message_id): {thread_id} | Aggregated Score: {agg_score:.4f}")
    
    # Fetch parent message
    cur.execute("SELECT text FROM messages WHERE message_id = %s", (thread_id,))
    parent = cur.fetchone()
    if parent:
        print(f"\n[PARENT] {parent[0]}")
    
    # Fetch child messages for this thread (if any)
    cur.execute("SELECT message_id, text FROM messages WHERE parent_id = %s ORDER BY created", (thread_id,))
    children = cur.fetchall()
    if children:
        for child in children:
            print(f"[CHILD] ({child[0]}) {child[1]}")
    else:
        print("[INFO] No child messages found.")
    print("=" * 80 + "\n")

# Close database connection
cur.close()
conn.close()
