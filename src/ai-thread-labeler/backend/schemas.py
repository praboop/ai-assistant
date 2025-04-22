from pydantic import BaseModel, ConfigDict, validator
from typing import List, Optional

class ThreadLabelBase(BaseModel):
    message_id: str
    label: str
    confidence_score: Optional[float] = None
    solution_message_id: Optional[str] = None
    reviewed: bool = False

    model_config = ConfigDict(from_attributes=True)

class ThreadLabelUpdateItem(BaseModel):
    message_id: str
    label: str
    confidence_score: float
    reviewed: bool

    @validator('label')
    def label_must_be_valid(cls, v):
        allowed = ['question', 'answer', 'clarification']
        if v not in allowed:
            raise ValueError(f"Label must be one of {allowed}")
        return v

    @validator('confidence_score')
    def confidence_must_be_in_range(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v

class ThreadLabelsUpdate(BaseModel):
    thread_parent_id: str  # The message_id of the parent message for the thread
    updates: List[ThreadLabelUpdateItem]
    
    @validator('updates')
    def check_question_consistency(cls, updates, values):
        thread_parent_id = values.get('thread_parent_id')
        for item in updates:
            # For a "question", the message_id must equal the thread_parent_id
            if item.label == "question" and item.message_id != thread_parent_id:
                raise ValueError(f"For a label 'question', message_id must match the thread_parent_id ({thread_parent_id}).")
        return updates