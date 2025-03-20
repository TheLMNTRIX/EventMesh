from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException
from app.services import firebase_service

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
    bio: Optional[str] = None
    mutual_interests: Optional[List[str]] = None
    mutual_connections: Optional[int] = None
    conversation_starters: Optional[List[str]] = None
    events_in_common: Optional[int] = None
    score: Optional[float] = None

router = APIRouter()

@router.get("/activity/{user_id}")
async def get_connections_activity(
    user_id: str,
    limit: int = Query(20, le=100, description="Maximum number of activities to return"),
    days: int = Query(30, le=90, description="Number of days to look back")
):
    """
    Get a feed of recent activities from the user's connections
    
    This endpoint returns a chronological feed of activities performed by the 
    user's connections, such as RSVPing to events.
    
    Activities are sorted by time, with the most recent appearing first.
    """
    # Validate user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's connections
    connections = await firebase_service.get_user_connections(user_id, status="accepted")
    connection_ids = [conn["from_user_id"] if conn["to_user_id"] == user_id else conn["to_user_id"] 
                      for conn in connections]
    
    if not connection_ids:
        return []
    
    # Get recent events (within specified days)
    look_back_date = datetime.now() - timedelta(days=days)
    events = await firebase_service.get_events(
        {"start_date": look_back_date},
        limit=100
    )
    
    # Activity feed to return
    activity_feed = []
    
    # For each event, get attendees that are connections of the user
    for event in events:
        event_id = event.get("id")
        event_attendees = await firebase_service.get_event_attendees(event_id)
        
        # Filter to only include connections
        connection_attendees = [
            attendee for attendee in event_attendees
            if attendee.get("user_id") in connection_ids
        ]
        
        # Get connection details and create activity objects
        for attendee in connection_attendees:
            connection_id = attendee.get("user_id")
            connection = await firebase_service.get_user(connection_id)
            
            if connection:
                # Get and parse RSVP date
                rsvp_date = attendee.get("rsvp_date")
                
                # Skip if no RSVP date
                if not rsvp_date:
                    continue
                
                # Convert string dates to datetime objects if needed
                if isinstance(rsvp_date, str):
                    try:
                        rsvp_date = datetime.fromisoformat(rsvp_date.replace('Z', '+00:00'))
                        rsvp_date = rsvp_date.replace(tzinfo=None)  # Make naive
                    except ValueError:
                        continue
                
                # Skip if RSVP is older than the look-back period
                if rsvp_date < look_back_date:
                    continue
                
                activity = {
                    "activity_type": "event_rsvp",
                    "timestamp": rsvp_date,
                    "connection": {
                        "user_id": connection_id,
                        "display_name": connection.get("display_name", "Unknown User"),
                        "profile_image_url": connection.get("profile_image_url")
                    },
                    "event": {
                        "id": event_id,
                        "title": event.get("title"),
                        "start_time": event.get("start_time"),
                        "end_time": event.get("end_time"),
                        "venue_name": event.get("venue", {}).get("name"),
                        "image_url": event.get("image_url")
                    },
                    "action": f"RSVP'd {attendee.get('status', 'attending')}"
                }
                
                activity_feed.append(activity)
    
    # Sort by timestamp (most recent first)
    activity_feed.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
    
    # Return limited number of activities
    return activity_feed[:limit]

__all__ = ["ConnectionStatus", "ConnectionRequest", "ConnectionResponse", "ConnectionSuggestion", "ConnectionRecommendation"]