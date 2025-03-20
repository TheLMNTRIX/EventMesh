from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class ConnectionStatus(BaseModel):
    status: Optional[str] = None  # "pending", "accepted", "declined", "blocked"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ConnectionRequest(BaseModel):
    from_user_id: Optional[str] = None  # Add this field
    to_user_id: Optional[str] = None

class ConnectionResponse(BaseModel):
    request_id: Optional[str] = None
    user_id: Optional[str] = None  # ID of the user responding (moved from query param)
    status: Optional[str] = None  # "accept" or "decline"

class ConnectionSuggestion(BaseModel):
    user_id: Optional[str] = None
    mutual_interests: Optional[List[str]] = None
    common_events: Optional[int] = None
    mutual_connections: Optional[int] = None

class ConnectionRecommendation(BaseModel):
    connection_id: Optional[str] = None
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    mutual_interests: Optional[List[str]] = None
    conversation_starters: Optional[List[str]] = None
    events_in_common: Optional[int] = None


__all__ = ["ConnectionStatus", "ConnectionRequest", "ConnectionResponse", "ConnectionSuggestion", "ConnectionRecommendation"]