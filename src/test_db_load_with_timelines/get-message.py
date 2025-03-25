import requests
import psycopg2
import time
from datetime import datetime
from collections import defaultdict
from config import BASE_URL, HEADERS, ROOMS, DB_CONFIG, MAX_RESULTS, START_DATE, END_DATE

def get_messages(room_id, start_date, end_date, max_results=MAX_RESULTS):
    """ Fetch messages from a Webex space within a date range, writing to DB in blocks. """
    url = f"{BASE_URL}?roomId={room_id}&max={max_results}"
    
    if start_date:
        url += f"&since={start_date}"
    elif end_date:
        url += f"&before={end_date}"

    fetched_count = 0
    total_inserted = 0

    while url:
        print(f"[DEBUG] Fetching from URL: {url}")
        start_time = time.time()
        
        try:
            response = requests.get(url, headers=HEADERS)
            elapsed = time.time() - start_time
        except requests.RequestException as e:
            print(f"[ERROR] Request failed: {e}")
            return False

        if response.status_code != 200:
            print(f"[ERROR] API returned {response.status_code}: {response.text}")
            return False

        data = response.json()
        messages = data.get("items", [])
        fetched_count += len(messages)

        print(f"[INFO] Fetched {len(messages)} messages in {elapsed:.2f}s (Total: {fetched_count})")

        if not messages:
            print("[DEBUG] No more messages found, stopping pagination.")
            break

        # Stop fetching if messages are older than START_DATE
        messages = [msg for msg in messages if msg.get("created", "9999-12-31") >= start_date]
        if not messages:
            print("[DEBUG] All remaining messages are older than START_DATE. Stopping fetch.")
            break

        inserted_per_date = insert_messages(messages, room_id)
        if inserted_per_date is False:
            print("[ERROR] Database insertion failed. Exiting.")
            return False  # Stop execution on DB failure

        total_inserted += sum(inserted_per_date.values())

        # Log inserted count per date
        for date, count in inserted_per_date.items():
            print(f"[INFO] {date} - {count} messages inserted.")

        # Pagination handling
        link_header = response.headers.get("Link")
        if link_header:
            next_link = [link.split(";")[0].strip("<>") for link in link_header.split(",") if 'rel="next"' in link]
            url = next_link[0] if next_link else None
        else:
            url = None  # No more pages

    print(f"[INFO] Completed fetching for room {room_id}. Total inserted: {total_inserted}")
    return True


def insert_messages(messages, room_id):
    """ Insert fetched messages into PostgreSQL, ensuring space exists. """
    if not messages:
        print("[DEBUG] No messages to insert.")
        return {}

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    inserted_per_date = defaultdict(int)  # Dictionary to track inserted count per date

    try:
        # Ensure the space exists in the 'spaces' table
        cursor.execute("SELECT COUNT(*) FROM spaces WHERE room_id = %s;", (room_id,))
        space_exists = cursor.fetchone()[0]

        if not space_exists:
            print(f"[WARNING] Space {room_id} is missing in 'spaces'. Inserting now.")
            cursor.execute("""
                INSERT INTO spaces (room_id, space_name)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
            """, (room_id, "Unknown Space"))  # Replace "Unknown Space" if you have a real name

        for message in messages:
            message_id = message.get("id")
            space_id = message.get("roomId")
            person_id = message.get("personId")
            person_email = message.get("personEmail")
            parent_id = message.get("parentId")
            text = message.get("text")
            created = message.get("created")

            if text is None:
                print(f"[WARNING] Skipping message {message_id} (empty text)")
                continue

            # Convert created timestamp to just the date (YYYY-MM-DD)
            created_date = created.split("T")[0]

            cursor.execute("""
                INSERT INTO messages (message_id, space_id, person_id, person_email, parent_id, text, created)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_id) DO NOTHING;
            """, (message_id, space_id, person_id, person_email, parent_id, text, created))

            inserted_per_date[created_date] += 1  # Track count per date

        conn.commit()

    except psycopg2.Error as e:
        print(f"[ERROR] Database error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()

    return inserted_per_date


if __name__ == "__main__":
    for room_id, room_name in ROOMS.items():
        print(f"[INFO] Processing room: {room_name} ({room_id})")
        get_messages(room_id, START_DATE, END_DATE)
