from fastapi import FastAPI, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from backend import models, crud, schemas
from backend.db import SessionLocal, engine

# Create all tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Thread Labeler Backend")

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
