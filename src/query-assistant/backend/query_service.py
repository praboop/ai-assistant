import numpy as np
import psycopg2
from psycopg2 import OperationalError, Error
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import sys
import os
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../embedding-service')))
from config import DB_CONFIG, FAISS_INDEX_PATH, FAISS_ID_MAP_PATH

model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
index = faiss.read_index(FAISS_INDEX_PATH)

with open(FAISS_ID_MAP_PATH, "rb") as f:
    id_map = pickle.load(f)

def get_thread_response(query: str):
    try:
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
                print(f"🧭 FAISS match: idx={idx} → message_id={msg_id}")
            else:
                print(f"⚠️ No mapping found for FAISS index {idx}")

        if not parent_ids:
            print("❌ No matching parent message_ids found in FAISS results.")
            return None

        # Step 3: DB lookup
        connection = None
        try:
            connection = psycopg2.connect(**DB_CONFIG)
            cursor = connection.cursor()

            for i, parent_id in enumerate(parent_ids):
                faiss_score = D[0][i]
                print(f"\n🗂 Checking thread for parent_id: {parent_id} (FAISS score: {faiss_score:.4f})")

                # Fetch the parent question text (thread question)
                try:
                    cursor.execute("""
                        SELECT text FROM messages
                        WHERE message_id = %s
                    """, (parent_id,))
                    parent_row = cursor.fetchone()
                    if not parent_row:
                        print(f"⚠️ No parent message found for parent_id={parent_id}. Skipping.")
                        continue
                    thread_question = parent_row[0]
                except Error as parent_query_err:
                    print(f"❌ Failed to fetch parent question for parent_id={parent_id}: {parent_query_err}")
                    continue

                # Fetch child messages
                try:
                    cursor.execute("""
                        SELECT m.message_id, m.text, l.label
                        FROM messages m
                        LEFT JOIN thread_labels l ON m.message_id = l.message_id
                        WHERE m.parent_id = %s
                        ORDER BY m.created
                    """, (parent_id,))
                    rows = cursor.fetchall()
                except Error as child_query_err:
                    print(f"❌ Database query failed for children of parent_id={parent_id}: {child_query_err}")
                    continue  # Try next thread

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
                        "thread_question": thread_question,
                        "answer": answer,
                        "follow_ups": follow_ups,
                        "faiss_score": float(faiss_score)
                    }
                else:
                    print(f"❌ No labeled answer found for thread {parent_id}")

        except OperationalError as conn_err:
            print(f"\n❌ Could not connect to PostgreSQL database: {conn_err}")
        except Error as db_err:
            print(f"\n❌ General database error: {db_err}")
        finally:
            if connection:
                connection.close()
                print("🔒 Database connection closed.")

        print("❌ No relevant thread with answer found.")
        return None

    except Exception as e:
        print("\n❌ Unexpected error in get_thread_response():")
        traceback.print_exc()
        return None
