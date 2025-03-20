from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.event import EventCreate, EventUpdate, Event, EventRSVP, EventFilter
from app.services.firebase_service import firebase_service
from app.services.recommendation_service import recommendation_service
from app.utils.validators import validate_event_dates, validate_coordinates, validate_rsvp_status
from app.utils.location_utils import filter_events_by_distance

router = APIRouter()

@router.post("/", response_model=Event, status_code=201)
async def create_event(event: EventCreate):
    """Create a new event"""
    # Validate dates
    if not validate_event_dates(event.start_time, event.end_time):
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    # Validate coordinates
    if not validate_coordinates(event.venue.latitude, event.venue.longitude):
        raise HTTPException(status_code=400, detail="Invalid coordinates")
    
    # Prepare event data
    event_data = event.model_dump()
    
    # Create event
    created_event = await firebase_service.create_event(event_data)
    return created_event

@router.get("/", response_model=List[Event])
async def get_events(
    categories: Optional[List[str]] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    max_distance_km: Optional[float] = Query(10.0),
    free_only: Optional[bool] = Query(False),
    limit: int = Query(50, le=100)
):
    """
    Get events with optional filtering
    """
    # Prepare filters
    filters = {}
    if categories:
        filters["categories"] = categories
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if free_only:
        filters["free_only"] = free_only
    
    # Get events from database
    events = await firebase_service.get_events(filters, limit=limit)
    
    # Apply location filtering if coordinates provided
    if latitude is not None and longitude is not None:
        if not validate_coordinates(latitude, longitude):
            raise HTTPException(status_code=400, detail="Invalid coordinates")
        
        events = filter_events_by_distance(events, latitude, longitude, max_distance_km)
    
    return events

@router.get("/recommendations")
async def get_event_recommendations(
    user_id: str,
    latitude: float,
    longitude: float,
    max_distance: Optional[float] = Query(10.0),
    limit: int = Query(20, le=50)
):
    """
    Get personalized event recommendations based on user interests and location
    """
    # Validate user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate coordinates
    if not validate_coordinates(latitude, longitude):
        raise HTTPException(status_code=400, detail="Invalid coordinates")
    
    # Get recommendations
    recommendations = await recommendation_service.get_event_recommendations(
        user_id, latitude, longitude, max_distance, limit
    )
    
    return recommendations

@router.get("/{event_id}", response_model=Event)
async def get_event(event_id: str):
    """Get event by ID"""
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.put("/{event_id}", response_model=Event)
async def update_event(event_id: str, event_update: EventUpdate):
    """Update event information"""
    # Check if event exists
    existing_event = await firebase_service.get_event(event_id)
    if not existing_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Filter out None values
    update_data = {k: v for k, v in event_update.model_dump().items() if v is not None}
    
    # Validate dates if both are provided
    if "start_time" in update_data and "end_time" in update_data:
        if not validate_event_dates(update_data["start_time"], update_data["end_time"]):
            raise HTTPException(status_code=400, detail="End time must be after start time")
    
    # Validate venue coordinates if provided
    if "venue" in update_data:
        venue = update_data["venue"]
        if not validate_coordinates(venue.latitude, venue.longitude):
            raise HTTPException(status_code=400, detail="Invalid coordinates")
    
    # Update event
    updated_event = await firebase_service.update_event(event_id, update_data)
    return updated_event

@router.delete("/{event_id}")
async def delete_event(event_id: str):
    """Delete an event"""
    # Check if event exists
    existing_event = await firebase_service.get_event(event_id)
    if not existing_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete event
    result = await firebase_service.delete_event(event_id)
    return {"status": "success", "message": "Event deleted"}

@router.post("/{event_id}/rsvp")
async def update_event_rsvp(event_id: str, user_id: str, rsvp_data: EventRSVP):
    """Update a user's RSVP status for an event"""
    # Check if event exists
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # We only accept "attending" status now
    if rsvp_data.status != "attending":
        raise HTTPException(status_code=400, detail="Only 'attending' status is supported")
    
    # Update RSVP
    result = await firebase_service.update_event_rsvp(event_id, user_id, rsvp_data.status)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to update RSVP")
    
    return {
        "status": "success",
        "message": "User is now attending this event",
        "event_id": event_id,
        "user_id": user_id
    }

@router.get("/{event_id}/attendees")
async def get_event_attendees(
    event_id: str,
    status: Optional[str] = Query(None, description="Filter by status: attending, interested, declined")
):
    """Get list of attendees for an event"""
    # Check if event exists
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get attendees
    attendees = await firebase_service.get_event_attendees(event_id, status)
    
    # Enrich with user details
    enriched_attendees = []
    for attendee in attendees:
        user_id = attendee["user_id"]
        user_details = await firebase_service.get_user(user_id)
        if user_details:
            enriched_attendee = {
                "user_id": user_id,
                "display_name": user_details.get("display_name", "Unknown"),
                "profile_image_url": user_details.get("profile_image_url"),
                "status": attendee["status"],
                "rsvp_date": attendee.get("rsvp_date")
            }
            enriched_attendees.append(enriched_attendee)
    
    return enriched_attendees

# Make sure to export router explicitly
__all__ = ["router"]