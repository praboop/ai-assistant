from sqlalchemy.orm import Session
from typing import List
from . import models, schemas

def get_all_thread_labels(db: Session) -> List[schemas.ThreadLabelBase]:
    thread_labels = db.query(models.ThreadLabels).all()
    # Convert each SQLAlchemy model to a Pydantic model using `from_orm`
    return [schemas.ThreadLabelBase.from_orm(label) for label in thread_labels]

def get_thread_labels_by_parent(db: Session, parent_message_id: str) -> List[schemas.ThreadLabelBase]:
    thread_labels = db.query(models.ThreadLabels).filter(models.ThreadLabels.message_id == parent_message_id).all()
    # Convert each SQLAlchemy model to a Pydantic model using `from_orm`
    return [schemas.ThreadLabelBase.from_orm(label) for label in thread_labels]
