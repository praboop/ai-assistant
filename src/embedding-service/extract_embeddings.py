import psycopg2
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer
import numpy as np
from config import DB_CONFIG

# Load the sentence transformer model
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2") 

# Connect to PostgreSQL
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Fetch messages that don't have embeddings
cur.execute("""
    SELECT message_id, text FROM messages
    WHERE message_id NOT IN (SELECT message_id FROM embeddings)
""")
messages = cur.fetchall()

if messages:
    data_to_insert = []
    
    for msg_id, text in messages:
        embedding = model.encode(text)  # Convert text to vector
        data_to_insert.append((msg_id, embedding.tolist()))

    # Insert embeddings into the database
    execute_values(cur, """
        INSERT INTO embeddings (message_id, vector)
        VALUES %s
    """, data_to_insert, template="(%s, %s)")

    conn.commit()
    print(f"Inserted {len(data_to_insert)} embeddings.")

else:
    print("No new messages to process.")

cur.close()
conn.close()
