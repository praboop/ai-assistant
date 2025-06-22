# config.py
import os

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "core-team-ai-assistant",
    "user": "core_user",
    "password": "BjqXmDcSWYpUf4J7UY7DKr"
}

FAISS_INDEX_PATH="/Users/pperiasa/git/ai-assistant/src/embedding-service/faiss_index_finetuned.bin"
#FAISS_ID_MAP_PATH="/Users/pperiasa/git/ai-assistant/src/embedding-service/faiss_index_finetuned.ids"
FAISS_ID_MAP_PATH="/Users/pperiasa/git/ai-assistant/src/embedding-service/faiss_id_map.pkl"