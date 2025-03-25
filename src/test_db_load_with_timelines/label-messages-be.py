from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = FastAPI()

# Load SBERT model for text embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")

DB_CONFIG = {
    "dbname": "core-team-ai-assistant",
    "user": "core_user",
    "password": "BjqXmDcSWYpUf4J7UY7DKr",
    "host": "localhost",
    "port": 5432
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# List of possible topic labels
TOPIC_LABELS = ["Networking Issue", "API Failure", "General Query", "Configuration Problem"]

# Model for labeling request
class ThreadLabel(BaseModel):
    thread_id: str
    topic_label: str
    solution_message_id: str = None
    solution_confidence: float = 1.0

def predict_topic_label(messages):
    """ Predict thread topic label using SBERT similarity """
    thread_text = " ".join([msg["text"] for msg in messages])
    thread_embedding = model.encode([thread_text])

    # Predefined topic embeddings
    topic_embeddings = model.encode(TOPIC_LABELS)
    similarities = cosine_similarity(thread_embedding, topic_embeddings)[0]

    # Select best topic
    best_topic = TOPIC_LABELS[np.argmax(similarities)]
    return best_topic

def predict_solution_message(messages):
    """ Identify the most likely solution message """
    solution_keywords = ["fixed", "resolved", "worked", "confirmed", "solution", "answer", "defect"]
    best_message = None
    best_score = 0

    for msg in messages:
        score = sum(1 for word in solution_keywords if word in msg["text"].lower())
        if score > best_score:
            best_message = msg["message_id"]
            best_score = score

    confidence = best_score / len(solution_keywords) if best_message else 0
    return best_message, confidence

@app.get("/threads/unlabeled")
def get_unlabeled_threads():
    """ Fetch unlabeled threads and apply AI predictions """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT t.thread_id, m.message_id, m.person_email, m.text, m.created
        FROM messages m
        JOIN threads t ON m.thread_id = t.thread_id
        LEFT JOIN thread_labels tl ON t.thread_id = tl.thread_id
        WHERE tl.thread_id IS NULL
        ORDER BY m.created;
    """)
    rows = cur.fetchall()
    conn.close()

    threads = {}
    for thread_id, message_id, email, text, created in rows:
        if thread_id not in threads:
            threads[thread_id] = []
        threads[thread_id].append({
            "message_id": message_id,
            "email": email,
            "text": text,
            "created": created
        })

    # Apply AI predictions
    ai_labeled_threads = {}
    for thread_id, messages in threads.items():
        predicted_label = predict_topic_label(messages)
        predicted_solution, confidence = predict_solution_message(messages)

        ai_labeled_threads[thread_id] = {
            "messages": messages,
            "predicted_label": predicted_label,
            "predicted_solution": predicted_solution,
            "confidence": confidence
        }

    return ai_labeled_threads

@app.post("/threads/label")
def label_thread(label: ThreadLabel):
    """ Store thread labels in DB """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO thread_labels (thread_id, topic_label, solution_message_id, solution_confidence)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (thread_id) DO UPDATE
            SET topic_label = EXCLUDED.topic_label,
                solution_message_id = EXCLUDED.solution_message_id,
                solution_confidence = EXCLUDED.solution_confidence;
        """, (label.thread_id, label.topic_label, label.solution_message_id, label.solution_confidence))
        
        conn.commit()
        return {"message": "Label saved successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
