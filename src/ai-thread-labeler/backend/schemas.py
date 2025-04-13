from pydantic import BaseModel, ConfigDict
from typing import Optional

class ThreadLabelBase(BaseModel):
    message_id: str
    label: str
    confidence_score: Optional[float] = None
    solution_message_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
