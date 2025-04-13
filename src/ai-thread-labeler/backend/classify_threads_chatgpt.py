import os
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Messages, ThreadLabels

from openai import OpenAI  # New OpenAI SDK client-based import

# Add the path to embedding-service to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../embedding-service')))
from config import DB_CONFIG

# Database setup
DATABASE_URL = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found in environment variables!")

# New OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


def fetch_thread(parent_msg):
    thread = [parent_msg]
    children = session.query(Messages).filter(Messages.parent_id == parent_msg.message_id).order_by(Messages.created).all()
    thread.extend(children)
    return thread


def format_thread_prompt(thread):
    prompt = "Classify each message in this thread as either 'question', 'answer', or 'clarification'.\n\n"
    prompt += "Thread:\n"
    for i, msg in enumerate(thread):
        role = "Parent" if i == 0 else "Reply"
        prompt += f"{i + 1}. ({role}) {msg.text.strip()}\n"
    prompt += (
        "\nRespond as JSON list like:\n"
        '[{"message_id": "abc123", "label": "question"}, {"message_id": "def456", "label": "answer"}]'
    )
    return prompt


def call_chatgpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"❌ Error calling OpenAI: {e}")
        return None


def manual_classification(thread):
    print("\n🛠️ Manual classification required:")
    labels = []
    for msg in thread:
        print(f"\nMessage: {msg.text.strip()}")
        label = input("Label (question/answer/clarification): ").strip().lower()
        labels.append({
            "message_id": msg.message_id,
            "label": label
        })
    return labels


def insert_labels(label_data):
    for entry in label_data:
        label = ThreadLabels(
            message_id=entry["message_id"],
            label=entry["label"],
            confidence_score=1.0 if entry.get("manual") else 0.95  # AI < 1.0
        )
        session.merge(label)  # Upsert
    session.commit()


def classify_all_threads():
    parents = session.query(Messages).filter(Messages.parent_id == None).all()
    print(f"📄 Found {len(parents)} parent messages.\n")

    for parent in parents:
        thread = fetch_thread(parent)
        prompt = format_thread_prompt(thread)
        print(f"\n🔍 Processing thread: {parent.message_id[:8]} with {len(thread)} messages")

        label_data = call_chatgpt(prompt)

        if not label_data or not isinstance(label_data, list):
            label_data = manual_classification(thread)
            for item in label_data:
                item["manual"] = True

        insert_labels(label_data)
        print("✅ Labels inserted.\n")


if __name__ == "__main__":
    classify_all_threads()
