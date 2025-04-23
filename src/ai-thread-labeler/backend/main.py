from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from backend import models, crud, schemas
from backend.db import SessionLocal, engine
from fastapi.responses import HTMLResponse
from fastapi import Request
from backend.query_service import QueryService
from fastapi import Body
import os
import json
from . import models

# Create all tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Thread Labeler Backend")

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/thread_label_review"))

app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

router = APIRouter()

query_service = QueryService()

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
                "messages": [],
                "created": None  # We'll fill this in later with parent message timestamp
            }

        label = labels.get(msg.message_id)
        threads[thread_id]["messages"].append({
            "message_id": msg.message_id,
            "text": msg.text,
            "label": label.label if label else None,
            "confidence": label.confidence_score if label else None,
            "reviewed": label.reviewed if label else None,
            "created": msg.created.isoformat()  # optional: include per-message timestamp too
        })

    # Fill in thread-level created timestamp using the parent message's created date
    for thread in threads.values():
        parent_msg = next((m for m in messages if m.message_id == thread["id"]), None)
        if parent_msg:
            thread["created"] = parent_msg.created.isoformat()

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

@app.post("/api/thread_labels/update")
def update_thread_labels(data: schemas.ThreadLabelsUpdate, db: Session = Depends(get_db)):
    # Get all message_ids in the thread (parent + children)
    thread_msg_ids = db.query(models.Messages.message_id).filter(
        (models.Messages.parent_id == data.thread_parent_id) | (models.Messages.message_id == data.thread_parent_id)
    ).all()
    # Flatten result tuples into a set
    thread_msg_ids = {row[0] for row in thread_msg_ids}
    if not thread_msg_ids:
        raise HTTPException(status_code=404, detail="Thread messages not found for the given parent_message_id")

    # Iterate over each update item and validate that the updated message belongs to the thread.
    for update in data.updates:
        if update.message_id not in thread_msg_ids:
            raise HTTPException(status_code=400, detail=f"Message ID {update.message_id} is not part of the thread {data.thread_parent_id}")

        # Retrieve the existing label record (if any)
        label_record = db.query(models.ThreadLabels).filter(models.ThreadLabels.message_id == update.message_id).first()
        if label_record:
            label_record.label = update.label
            label_record.confidence_score = update.confidence_score
            label_record.reviewed = update.reviewed
        else:
            new_record = models.ThreadLabels(
                message_id=update.message_id,
                label=update.label,
                confidence_score=update.confidence_score,
                reviewed=update.reviewed
            )
            db.add(new_record)

    db.commit()

    # Determine solution_message_id for the thread:
    # Among all records for messages in the thread with label "answer", pick the one with the highest confidence.
    answer_records = db.query(models.ThreadLabels).filter(
        models.ThreadLabels.message_id.in_(thread_msg_ids),
        models.ThreadLabels.label == "answer"
    ).all()

    if answer_records:
        best_answer = max(answer_records, key=lambda r: r.confidence_score)
        db.query(models.ThreadLabels).filter(
            models.ThreadLabels.message_id.in_(thread_msg_ids)
        ).update({models.ThreadLabels.solution_message_id: best_answer.message_id}, synchronize_session=False)
    else:
        db.query(models.ThreadLabels).filter(
            models.ThreadLabels.message_id.in_(thread_msg_ids)
        ).update({models.ThreadLabels.solution_message_id: None}, synchronize_session=False)

    db.commit()

    return {"success": True, "updated": len(data.updates)}  


@router.post("/api/query")
def query_thread_similarities(payload: dict = Body(...)):
    query_text = payload.get("query")
    if not query_text:
        raise HTTPException(status_code=400, detail="Missing query text")

    # Just a stub — will call embedding + FAISS next
    return {"message": "Query endpoint is live", "query": query_text}    

app.include_router(router)