from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from backend import models, crud, schemas
from backend.db import SessionLocal, engine
from fastapi.responses import HTMLResponse
from fastapi import Request
import os
from . import models

# Create all tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Thread Labeler Backend")

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/thread_label_review"))

app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

router = APIRouter()


# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    index_path = os.path.join(frontend_dir, "index.html")
    try:
        with open(index_path, "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="Frontend not found", status_code=404)  

@router.get("/api/threads")
def get_threads(db: Session = Depends(get_db)):
    messages = db.query(models.Messages).all()
    labels = {label.message_id: label for label in db.query(models.ThreadLabels).all()}

    # Group by thread (using parent_id as thread root)
    threads = {}
    for msg in messages:
        thread_id = msg.parent_id if msg.parent_id else msg.message_id
        if thread_id not in threads:
            threads[thread_id] = {
                "id": thread_id,
                "messages": []
            }

        label = labels.get(msg.message_id)
        threads[thread_id]["messages"].append({
            "message_id": msg.message_id,
            "text": msg.text,
            "label": label.label if label else None,
            "confidence": label.confidence_score if label else None,
        })

    return list(threads.values())        

@app.get("/api/thread_labels", response_model=List[schemas.ThreadLabelBase])
def read_thread_labels(
    parent_message_id: Optional[str] = Query(None, description="Filter by parent message ID"),
    db: Session = Depends(get_db)  # ✅ Use Depends instead of next(get_db())
):
    try:
        if parent_message_id:
            labels = crud.get_thread_labels_by_parent(db, parent_message_id)
        else:
            labels = crud.get_all_thread_labels(db)
        return labels
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)