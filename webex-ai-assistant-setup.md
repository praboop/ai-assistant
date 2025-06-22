# 🚀 Setup Guide for Webex AI Assistant

---

## 🧱 Milestone 1: Create Empty Database in Local Docker

1. **Run PostgreSQL with pgvector using Docker**  
   ```bash
   docker run -d \
     --name webex-space-ai-assistant \
     -p 5433:5432 \
     -e POSTGRES_USER=core_user \
     -e POSTGRES_PASSWORD=BjqXmDcSWYpUf4J7UY7DKr \
     -e POSTGRES_DB=core-team-ai-assistant \
     ankane/pgvector
   ```

2. **Enable the `vector` extension** in the database using SQL editor:
   ```sql
   CREATE EXTENSION vector;
   ```

3. **Set up Python environment**
   ```bash
   cd ai-thread-labeler
   source venv/bin/activate
   pip3 install -r requirements.txt
   ```

4. **Create tables**  
   ✅ **Preferred: Option 2 (Fresh Migration)**  
   - Delete existing migration scripts:
     ```bash
     rm backend/alembic/versions/*.py
     ```
   - Create new migration:
     ```bash
     alembic -c alembic.ini revision --autogenerate -m "initial"
     ```
   - Edit the generated migration file to include:
     ```python
     import pgvector
     from pgvector.sqlalchemy import Vector
     ```
   - Apply migration:
     ```bash
     alembic -c alembic.ini upgrade head
     ```

   🔁 Optionally, use existing migration:
   ```bash
   alembic -c alembic.ini upgrade head
   ```

5. ✅ **Verify** all tables from `model.py` are created in your database.

---

## 💬 Milestone 2: Load Webex Space Messages into `messages` Table

1. Open `config.py` in `webex_message_loader` and update:
   - Webex token
   - Space room ID
   - Start & end dates

2. To get your Webex token:
   - Login at [https://developer.webex.com](https://developer.webex.com)
   - Click your profile and copy the **Bearer Token**
   - Paste it into `config.py`

3. To get a **room ID**:
   - Use [List Rooms API](https://developer.webex.com/messaging/docs/api/v1/rooms/list-rooms)
   - Update the `room_id` in `config.py`

4. Run the loader:
   ```bash
   cd webex_message_loader
   source venv/bin/activate
   pip3 install -r requirements.txt
   python3 get-message.py
   ```

5. ✅ Verify data is inserted into the `messages` table.

---

## 🧠 Milestone 3: Label & Classify Messages

### 🔹 Approach 1: Semi-Automated Labelling
- **Thread label**: SBERT + cosine similarity  
- **Solution detection**: Heuristics on keywords like _"fixed", "resolved", "solution"_

Run:
```bash
cd webex_message_loader
python3 label-messages-be.py
python3 label-messages-fe.py
```

Then:
- Open browser
- Review & save message labels manually

---

### 🔸 Approach 2: Gemini-Powered AI Labelling (Preferred)

1. Get your **Gemini API Key** from Google AI Studio
2. Set up and run:
   ```bash
   cd ai-thread-labeler
   source venv/bin/activate
   cd backend
   export GEMINI_API_KEY=<your_key>
   python3 classify_threads.py
   ```

3. ✅ Verify data in `thread_labels` table

4. Start the backend server:
   ```bash
   cd backend
   uvicorn backend.main:app --reload
   ```

5. Open browser at [http://localhost:8000/](http://localhost:8000/)
   - Review and validate AI labels
   - Save them

---

## 🧬 Milestone 4: Build Embeddings & FAISS Index

1. Prepare environment:
   ```bash
   cd embedding-service
   /opt/homebrew/bin/python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Extract embeddings:
   ```bash
   python3 extract_embeddings.py
   ```

3. Create FAISS index + ID map:
   ```bash
   python3 setup_faiss_index_and_idmap.py
   ```

4. Verify accuracy of embedding matches:
   ```bash
   python3 verify_faiss_finetuned.py
   ```

---

## 💡 Milestone 5: Run the Query Assistant

1. Launch the assistant backend:
   ```bash
   cd query-assistant
   source venv/bin/activate
   pip install -r requirements.txt
   cd backend
   uvicorn main:app --reload --port 8001
   ```

2. Open browser:
   [http://localhost:8001/](http://localhost:8001/)

3. ✅ Enter queries and review AI responses
