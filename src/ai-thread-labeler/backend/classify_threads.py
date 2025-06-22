import os
import sys
import json
import time
import requests
from sqlalchemy import create_engine, select, exists
from sqlalchemy.orm import sessionmaker
from models import Messages, ThreadLabels, Base
from sqlalchemy import func

# Add path to config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../embedding-service')))
from config import DB_CONFIG

# DB Setup
DATABASE_URL = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Number of threads (with childrens) to be sent to gemini at a time
global_batch_size=5

# Gemini Config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# --- Core Functions --- #

def fetch_unlabeled_threads():
    parents = session.query(Messages).filter(Messages.parent_id == None).all()
    unlabeled_parents = []
    for parent in parents:
        already_labeled = session.query(
            exists().where(ThreadLabels.message_id == parent.message_id)
        ).scalar()
        if not already_labeled:
            unlabeled_parents.append(parent)
        if len(unlabeled_parents) >= global_batch_size:
            break
    return unlabeled_parents


def fetch_thread(parent_msg):
    thread = [parent_msg]
    children = session.query(Messages).filter(Messages.parent_id == parent_msg.message_id).order_by(Messages.created).all()
    thread.extend(children)
    return thread


def format_threads_prompt(threads):
    prompt_parts = []
    prompt_parts.append({
        "text": (
            "You will receive multiple message threads. Each thread contains a conversation "
            "consisting of a parent message and its replies.\n\n"
            "For each message in a thread, assign a label: 'question', 'clarification', or 'answer'.\n"
            "**There must be at most one 'answer' per thread, and it should have the highest confidence score.**\n"
            "Include a confidence_score (between 0.0 and 1.0) for each label.\n\n"
            "Return your answer as a JSON list like:\n"
            '[{"message_id": "abc123", "label": "question", "confidence_score": 0.93}, {"message_id": "def456", "label": "answer", "confidence_score": 0.98}]\n\n'
            "**Important**: Use the original message_id exactly as shown in the input.\n"
        )
    })

    for i, thread in enumerate(threads):
        prompt_parts.append({"text": f"Thread {i+1}:\n"})
        for j, msg in enumerate(thread):
            role = "Parent" if j == 0 else "Reply"
            prompt_parts.append({
                "text": f"{j+1}. ({role}) {msg.text.strip()} [message_id: {msg.message_id}]\n"
            })

    return {"contents": [{"parts": prompt_parts}]}


def call_gemini(prompt_body):
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(GEMINI_URL, headers=headers, json=prompt_body)
        response.raise_for_status()
        content = response.json()["candidates"][0]["content"]["parts"]
        if not content:
            raise ValueError("Gemini returned empty parts")
        global_batch_size = 5
        return content[0]["text"]
    except Exception as e:
        global_batch_size = 1
        print(f"❌ Gemini error: {e}")
        if 'response' in locals():
            print("📥 Response body:")
            print(response.text[:2000])
        return None


def parse_gemini_response(text):
    try:
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:].strip()
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3].strip()
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse Gemini response: {text}")
        raise


def insert_labels(label_data, thread_ids, prompt_body=None, gemini_response_text=None):
    thread_to_answers = {}

    for entry in label_data:

        message_id = entry["message_id"]
        label = entry["label"]
        confidence = entry.get("confidence_score", 0.95)

        # Confirm this ID exists in messages table
        exists_in_db = session.query(
            exists().where(Messages.message_id == message_id)
        ).scalar()

        if not exists_in_db:
            print("❌ ERROR: Gemini returned unknown message_id:")
            print(f"  message_id = {message_id}")
            print("🔎 Request sent to Gemini:")
            print(json.dumps(prompt_body, indent=2)[:3000])  # Trimmed for readability
            print("🔍 Response from Gemini:")
            print(gemini_response_text[:2000])  # Trimmed for readability
            continue  # Skip inserting invalid ID

        label_obj = ThreadLabels(
            message_id=message_id,
            label=label,
            confidence_score=confidence,
            solution_message_id=None
        )
        session.merge(label_obj)

        # Track possible answers for solution selection
        for parent in thread_ids:
            if message_id in thread_ids[parent]:
                thread_to_answers.setdefault(parent, []).append((message_id, confidence))

    for thread_id, answers in thread_to_answers.items():
        if not answers:
            continue
        solution_msg_id = max(answers, key=lambda x: x[1])[0]

        session.query(ThreadLabels).filter(
            ThreadLabels.message_id.in_(thread_ids[thread_id])
        ).update({ThreadLabels.solution_message_id: solution_msg_id}, synchronize_session=False)

    session.commit()


def print_status(batch_parents):
    total = session.query(Messages).filter(Messages.parent_id == None).count()
    labeled_parent_ids = session.query(Messages.message_id).filter(
        Messages.parent_id == None,
        Messages.message_id.in_(
            session.query(ThreadLabels.message_id)
        )
    ).count()
    remaining = total - labeled_parent_ids
    print(f"\n🧭 STATUS: {labeled_parent_ids}/{total} labeled | {remaining} remaining | {len(batch_parents)} in this batch\n")


# --- Main Execution --- #

def classify_all_threads():
    while True:
        parents = fetch_unlabeled_threads()
        if not parents:
            print("✅ All threads are already labeled.")
            break

        thread_batch = [fetch_thread(parent) for parent in parents]
        prompt_body = format_threads_prompt(thread_batch)

        print_status(parents)
        print(f"📤 Sending batch with {len(parents)} threads to Gemini...")

        response_text = call_gemini(prompt_body)
        if not response_text:
            print("⚠️ Skipping batch due to error.")
            time.sleep(5)
            continue

        try:
            label_data = parse_gemini_response(response_text)
        except json.JSONDecodeError:
            print("❌ Failed to parse Gemini response.")
            print("🔍 Gemini response:")
            print(response_text[:2000])
            continue

        if label_data:
            thread_ids = {
                thread[0].message_id: [msg.message_id for msg in thread]
                for thread in thread_batch
            }
            insert_labels(label_data, thread_ids, prompt_body, response_text)
            print(f"✅ Labeled {len(label_data)} messages in this batch.")
        else:
            print("⚠️ Manual inspection needed for Gemini response.")

        print("⏳ Waiting to respect rate limits...")
        time.sleep(5)

if __name__ == "__main__":
    classify_all_threads()
