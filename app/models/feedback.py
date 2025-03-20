from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class EventRating(BaseModel):
    event_id: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    comments: Optional[str] = None
    photos: Optional[List[str]] = None  # URLs of uploaded photos
    created_at: Optional[datetime] = Field(default_factory=datetime.now)

class EventFeedbackCreate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None

class EventFeedbackResponse(EventFeedbackCreate):
    event_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None


__all__ = ["EventRating", "EventFeedbackCreate", "EventFeedbackResponse"]
