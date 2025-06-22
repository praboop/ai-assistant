
# 🤖 Webex AI Assistant

A smart assistant that helps analyze, label, and respond to queries posted in Webex Spaces using AI models like **SBERT**, **Gemini**, and **FAISS** for semantic search and classification.

---

## 🚀 Overview

This project demonstrates how to build an AI-powered assistant that helps engineers respond to technical queries posted in Webex Spaces. By leveraging historical conversations and AI-driven thread understanding, the assistant can automatically detect, classify, and retrieve relevant past answers to assist with new queries.

The core idea is to emulate the behavior of a knowledgeable support agent who has full context of previous discussions — surfacing solutions that were already shared in the past.

While the current implementation targets engineering discussions within Webex Spaces — which are often nuanced and context-rich — the approach is especially well-suited for domains like contact centers, where the types of queries and responses are more structured and repetitive. In such scenarios, the assistant can be highly effective in reducing response time and improving consistency by surfacing the most relevant prior solutions from a finite solution space.

### Key capabilities
- 📥 Ingestion of messages from Webex Spaces  
- 🧠 AI-based thread classification and solution detection  
- 📈 Embedding-based semantic search using FAISS  
- 📝 Gemini-powered contextual rephrasing of matched responses  
- 🌐 Interactive web frontend for querying and reviewing AI suggestions


---

### Project Workflow
Note: If you are viewing this in vscode, install the  **Markdown Preview Mermaid Support** extension if needed.

```mermaid
flowchart TD
    subgraph Milestone_1[Milestone 1: Setup Database]
        A1[Start PostgreSQL Docker with pgvector]
        A2[Create vector extension]
        A3[Install Python dependencies]
        A4[Run Alembic migration]
    end

    subgraph Milestone_2[Milestone 2: Load Webex Messages]
        B1[Configure Webex Token & Room ID]
        B2[Set start/end date in config.py]
        B3[Run get-message.py]
        B4[Verify messages table]
    end

    subgraph Milestone_3[Milestone 3: Thread Labeling]
        C1[Option 1: Local SBERT+keywords]
        C2[Option 2: Gemini Classification]
        C3[Manual UI Review via FastAPI]
    end

    subgraph Milestone_4[Milestone 4: Build Embeddings + FAISS Index]
        D1[Extract SBERT embeddings]
        D2[Store vectors in DB]
        D3[Build FAISS index + ID map]
        D4[Test FAISS accuracy]
    end

    subgraph Milestone_5[Milestone 5: Run Query Assistant]
        E1[Start FastAPI backend]
        E2[User submits query]
        E3[Search FAISS for match]
        E4[Fetch thread response from DB]
        E5[Send prompt to Gemini]
        E6[Gemini returns JSON: response + score + reasoning]
        E7[Render result in HTML UI]
    end

    A1 --> A2 --> A3 --> A4 --> B1
    B1 --> B2 --> B3 --> B4 --> C1
    C1 --> C3
    C2 --> C3
    C3 --> D1 --> D2 --> D3 --> D4 --> E1
    E1 --> E2 --> E3 --> E4 --> E5 --> E6 --> E7
```

---

## 🧱 Project Structure

```plaintext
ai-assistant/
├── ai-thread-labeler/
│   ├── backend/                  # FastAPI backend with thread 
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── main.py               # API server
│   │   └── classify_threads.py   # Gemini-based classifier
│   └── frontend/
│       └── thread_label_review   # Manual solution review 
│
├── embedding-service/
│   ├── extract_embeddings.py     # Convert messages to embeddings
│   ├── setup_faiss_index_and_idmap.py  # Build and persist FAISS index
│   └── verify_faiss_finetuned.py # Test similarity ranking
│
├── query-assistant/
│   ├── main.py                   # Gemini query handler and UI backend
│   ├── templates/index.html      # Query response UI
│   └── config.py                 # DB and model paths
│
├── webex_message_loader/
│   ├── get-message.py            # Pull messages from Webex API
│   ├── label-messages-be.py      # Legacy backend classifier
│   ├── label-messages-fe.py      # Frontend JSON output for manual 
│   └── config.py                 # Webex token and room ID setup
│
│
├── README.md
└── webex-ai-assistant-setup.md   # Full setup guide for local development
```

---

## 🔧 Technologies Used

- **FastAPI** - Backend server
- **PostgreSQL** with **pgvector** - Vector DB storage
- **FAISS** - Semantic similarity search
- **Google Gemini API** - Natural language processing + reasoning
- **SBERT** - Sentence-BERT embeddings
- **Bootstrap 5** - Web UI styling
- **Webex API** - Message ingestion

---

## 🛠 Setup Instructions

Follow the step-by-step guide in [`webex-ai-assistant-setup.md`](webex-ai-assistant-setup.md) to:

1. Spin up PostgreSQL with `pgvector` extension.
2. Ingest Webex messages.
3. Classify threads via Gemini or SBERT.
4. Build FAISS index.
5. Run backend and frontend servers.
6. Start querying past issues.

---

## 📸 UI Preview

![Query Assistant Screenshot](docs/ui-screenshot.png) *(You can add your screenshot here)*

---

## ✅ Milestones

- ✅ Milestone 1: Setup database with vector support
- ✅ Milestone 2: Ingest and store messages
- ✅ Milestone 3: Classify threads and detect solutions
- ✅ Milestone 4: Build embeddings and FAISS index
- ✅ Milestone 5: Query assistant integration (UI + Gemini response)

---

## 👥 Contributing

Contributions are welcome! Please file issues or feature requests in GitHub or reach out to the maintainers.

---

## 📝 License


---

## ✨ Authors

- [Prabhu] — Built and maintained this project with 💡 and ☕
