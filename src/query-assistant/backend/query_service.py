import numpy as np
import psycopg2
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../embedding-service')))
from config import DB_CONFIG, FAISS_INDEX_PATH, FAISS_ID_MAP_PATH

# For testing a thread with question on logout api is getting identified
# TARGET_THREAD_ID = "Y2lzY29zcGFyazovL3VzL01FU1NBR0UvZjVhNDQyMjAtYjM5MC0xMWVmLWIwOTEtMzc5Zjk1YTk0Y2Y0"

# Load model and FAISS index
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
index = faiss.read_index(FAISS_INDEX_PATH)

# Load ID map
with open(FAISS_ID_MAP_PATH, "rb") as f:
    id_map = pickle.load(f)  # {faiss_idx: message_id}

def get_thread_response(query: str):
    print(f"\n🔍 Query: {query}")

    # Step 1: Embed the query
    query_vec = model.encode([query], normalize_embeddings=True).astype(np.float32)

    # Step 2: Search FAISS
    k = 5
    D, I = index.search(query_vec, k)

    print("📊 FAISS distances (similarity scores):", D[0])
    print("🔢 FAISS indexes:", I[0])

    parent_ids = []
    for idx in I[0]:
        if idx in id_map:
            msg_id = id_map[idx]
            parent_ids.append(msg_id)
            if 'TARGET_THREAD_ID' in globals():
                print(f"🧭 FAISS match: idx={idx} → message_id={msg_id} {'✅ MATCH' if msg_id == TARGET_THREAD_ID else ''}")
            else:
                print(f"🧭 FAISS match: idx={idx} → message_id={msg_id}")
        else:
            print(f"⚠️ No mapping found for FAISS index {idx}")

    if not parent_ids:
        print("❌ No matching parent message_ids found in FAISS results.")
        return None

    # Step 3: DB lookup
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    for i, parent_id in enumerate(parent_ids):
        faiss_score = D[0][i]  # Score corresponding to this match
        print(f"\n🗂 Checking thread for parent_id: {parent_id} (FAISS score: {faiss_score:.4f})")

        cursor.execute("""
            SELECT m.message_id, m.text, l.label
            FROM messages m
            LEFT JOIN thread_labels l ON m.message_id = l.message_id
            WHERE m.parent_id = %s
            ORDER BY m.created
        """, (parent_id,))
        rows = cursor.fetchall()

        if not rows:
            print("📭 No child messages found.")
            continue

        # Step 4: Process children
        answer = None
        follow_ups = []
        for message_id, text, label in rows:
            if label == "answer" and not answer:
                print(f"🔹 Child message: {message_id}, label={label}")
                answer = text
            elif label in {"clarification", "answer"}:
                follow_ups.append(text)

        if answer:
            print(f"✅ Answer found for thread {parent_id}")
            return {
                "thread_id": parent_id,
                "answer": answer,
                "follow_ups": follow_ups,
                "faiss_score": float(faiss_score)  # Convert numpy float32 to native float
            }
        else:
            print(f"❌ No labeled answer found for thread {parent_id}")

    print("❌ No relevant thread with answer found.")
    return None

