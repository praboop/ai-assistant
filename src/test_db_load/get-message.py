import requests
import psycopg2
import time
from config import BASE_URL, HEADERS, ROOMS, DB_CONFIG, MAX_RESULTS

def get_messages(room_id, max_results=MAX_RESULTS):
    """ Fetch messages from a Webex space, following pagination links. """
    url = f"{BASE_URL}?roomId={room_id}&max={max_results}"
    all_messages = []
    fetched_count = 0

    while url and fetched_count < 100:  # Prevent infinite loops
        start_time = time.time()
        response = requests.get(url, headers=HEADERS)
        elapsed = time.time() - start_time

        if response.status_code != 200:
            print(f"Error fetching messages: {response.text}")
            break

        data = response.json()
        messages = data.get("items", [])
        fetched_count += len(messages)
        all_messages.extend(messages)

        print(f"Fetched {fetched_count} messages in {elapsed:.2f}s from {url}")

        # Pagination handling
        link_header = response.headers.get("Link")
        if link_header:
            next_link = [link.split(";")[0].strip("<>") for link in link_header.split(",") if 'rel="next"' in link]
            url = next_link[0] if next_link else None
        else:
            url = None  # No more pages

    return all_messages


def insert_space(room_id, room_name):
    """ Insert a space into the `spaces` table if it doesn’t already exist. """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO spaces (room_id, space_name)
            VALUES (%s, %s)
            ON CONFLICT (room_id) DO NOTHING;
        """, (room_id, room_name))
        conn.commit()
        print(f"Inserted/verified space: {room_name} ({room_id})")

    except psycopg2.Error as e:
        print(f"Error inserting space {room_id}: {e}")

    finally:
        cursor.close()
        conn.close()


def insert_messages(messages, room_id):
    """ Insert fetched messages into PostgreSQL, handling constraints. """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    inserted_count = 0

    for i, message in enumerate(messages, start=1):
        try:
            message_id = message.get("id")
            space_id = message.get("roomId")
            person_id = message.get("personId")
            person_email = message.get("personEmail")
            parent_id = message.get("parentId")  # Extract `parentId`
            text = message.get("text")
            created = message.get("created")

            # Debugging output
            print(f"Processing Message ID: {message_id}, Parent ID: {parent_id}, Person Email: {repr(person_email)}")

            if person_email is None:
                print(f"Warning: Missing person_email for message {message_id}")

            cursor.execute("""
                INSERT INTO messages (message_id, space_id, person_id, person_email, parent_id, text, created)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_id) DO NOTHING;
            """, (message_id, space_id, person_id, person_email, parent_id, text, created))

            inserted_count += 1
            print(f"Inserted {i}/{len(messages)} message(s) for room {room_id}")

        except psycopg2.Error as e:
            print(f"Error inserting message {message_id}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"All messages from room {room_id} have been fetched and stored. Total inserted: {inserted_count}")


def get_thread_messages(room_id, parent_message_id):
    """ Fetch all messages that belong to a given thread. """
    url = f"{BASE_URL}?roomId={room_id}&parentId={parent_message_id}&max=100"
    thread_messages = []
    
    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Error fetching thread messages for {parent_message_id}: {response.text}")
            break

        data = response.json()
        messages = data.get("items", [])
        thread_messages.extend(messages)

        # Pagination handling for thread messages
        link_header = response.headers.get("Link")
        if link_header:
            next_link = [link.split(";")[0].strip("<>") for link in link_header.split(",") if 'rel="next"' in link]
            url = next_link[0] if next_link else None
        else:
            url = None  # No more pages

    return thread_messages


def process_rooms():
    """ Fetch and store messages for two threads and stop. """
    processed_threads = 0

    for room_id, room_name in ROOMS.items():
        if processed_threads >= 2:
            print("Processed two threads. Exiting.")
            break

        print(f"Processing room: {room_name} ({room_id})")

        # Insert space into the database before processing messages
        insert_space(room_id, room_name)

        messages = get_messages(room_id)

        # Process only top-level messages (new threads)
        thread_starters = [msg for msg in messages if msg.get("parentId") is None]
        
        for thread in thread_starters:
            if processed_threads >= 2:
                break

            thread_id = thread.get("id")
            print(f"Processing thread: {thread_id}")

            # Fetch entire thread
            thread_messages = get_thread_messages(room_id, thread_id)
            complete_thread = [thread] + thread_messages  # Include the first message and its replies

            insert_messages(complete_thread, room_id)
            processed_threads += 1

        if processed_threads >= 2:
            break


if __name__ == "__main__":
    process_rooms()
