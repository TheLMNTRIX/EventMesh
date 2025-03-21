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
    
    # Validate schedule items if provided
    if event.schedule:
        for item in event.schedule:
            # Check that each schedule item has valid start/end times
            if not validate_event_dates(item.start_time, item.end_time):
                raise HTTPException(status_code=400, detail="Schedule item end time must be after start time")
            
            # Check that schedule items are within the event time range
            if item.start_time < event.start_time or item.end_time > event.end_time:
                raise HTTPException(
                    status_code=400, 
                    detail="Schedule items must be within the event's start and end times"
                )
    
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
    
    # Ensure required fields are included in each event
    for event in events:
        # Ensure schedule is included
        if "schedule" not in event:
            event["schedule"] = []
        
        # Ensure image_url is included
        if "image_url" not in event:
            event["image_url"] = None
        
        # Ensure venue with coordinates is included
        if "venue" not in event:
            event["venue"] = {
                "name": None,
                "address": None,
                "latitude": None,
                "longitude": None
            }
        elif isinstance(event["venue"], dict):
            # Ensure venue has latitude and longitude
            if "latitude" not in event["venue"]:
                event["venue"]["latitude"] = None
            if "longitude" not in event["venue"]:
                event["venue"]["longitude"] = None
            if "name" not in event["venue"]:
                event["venue"]["name"] = None
            if "address" not in event["venue"]:
                event["venue"]["address"] = None
    
    return events



@router.get("/{event_id}", response_model=Event)
async def get_event(event_id: str):
    """Get event details by ID"""
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Ensure schedule is included in the response
    if "schedule" not in event:
        event["schedule"] = []
        
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

@router.get("/recommendations/{user_id}", response_model=List[Event])
async def get_event_recommendations(
    user_id: str,
    latitude: float = Query(..., description="User's current latitude"),
    longitude: float = Query(..., description="User's current longitude"),
    categories: Optional[List[str]] = Query(None, description="Filter by specific categories"),
    free_only: Optional[bool] = Query(False, description="Show only free events"),
    max_price: Optional[float] = Query(None, description="Maximum price of events"),
    distance: float = Query(10.0, description="Maximum distance in kilometers"),
    limit: int = Query(10, le=50, description="Maximum number of recommendations to return")
):
    """
    Get personalized event recommendations for a user
    
    This endpoint uses a recommendation engine that considers:
    - User interests
    - Social connections
    - Geographic proximity
    - Event timing
    - Categories (optional filter)
    - Price (optional filter)
    
    Returns events with a score indicating relevance and score_details showing component scores.
    """
    # Validate user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate coordinates
    if not validate_coordinates(latitude, longitude):
        raise HTTPException(status_code=400, detail="Invalid coordinates")
    
    # Get recommendations from the recommendation service
    recommended_events = await recommendation_service.get_event_recommendations(
        user_id=user_id,
        latitude=latitude,
        longitude=longitude,
        max_distance_km=distance,
        limit=limit
    )
    
    # Apply additional filtering based on optional parameters
    filtered_events = recommended_events
    
    # Sort by category match if categories are provided
    if categories:
        # Sort events by whether they match the requested categories
        # Events with matching categories come first, sorted by score
        # Then events without matching categories, sorted by score
        def category_match_sort_key(event):
            event_categories = set(event.get('category', []))
            requested_categories = set(categories)
            has_match = len(event_categories.intersection(requested_categories)) > 0
            # Return tuple: (has match (negative for sorting), score)
            # Using negative for has_match to sort True before False
            return (-int(has_match), -event.get('score', 0))
            
        filtered_events.sort(key=category_match_sort_key)
    
    # Filter by price if needed
    if free_only:
        filtered_events = [
            event for event in filtered_events 
            if not event.get('price') or event.get('price') == 0
        ]
    elif max_price is not None:
        filtered_events = [
            event for event in filtered_events 
            if not event.get('price') or event.get('price') <= max_price
        ]
    
    # Ensure all events have required fields to match the get_events response format
    for event in filtered_events:
        # Ensure schedule is included
        if "schedule" not in event:
            event["schedule"] = []
        
        # Ensure image_url is included
        if "image_url" not in event:
            event["image_url"] = None
        
        # Ensure venue with coordinates is included
        if "venue" not in event:
            event["venue"] = {
                "name": None,
                "address": None,
                "latitude": None,
                "longitude": None
            }
        elif isinstance(event["venue"], dict):
            # Ensure venue has all required fields
            if "latitude" not in event["venue"]:
                event["venue"]["latitude"] = None
            if "longitude" not in event["venue"]:
                event["venue"]["longitude"] = None
            if "name" not in event["venue"]:
                event["venue"]["name"] = None
            if "address" not in event["venue"]:
                event["venue"]["address"] = None
                
        # Ensure end_time is included
        if "end_time" not in event:
            # If no end_time, set it to 2 hours after start_time
            if "start_time" in event:
                start_time = event["start_time"]
                if isinstance(start_time, datetime):
                    event["end_time"] = start_time + timedelta(hours=2)
                else:
                    event["end_time"] = None
            else:
                event["end_time"] = None
    
    # Return filtered events, limited to requested count, still sorted by score
    return filtered_events[:limit]

@router.get("/{event_id}/match/{user_id}")
async def get_event_user_match_score(
    event_id: str,
    user_id: str,
    latitude: Optional[float] = Query(None, description="User's current latitude"),
    longitude: Optional[float] = Query(None, description="User's current longitude")
):
    """
    Get event details with personalized match score for a specific user
    
    This endpoint returns the full event details (like GET /events/{event_id}) 
    plus a match score indicating relevance to the user based on:
    - Interest match (user interests vs event categories)
    - Social match (friends attending)
    - Geographic proximity (if location provided)
    - Timing relevance
    """
    # Validate user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate event exists
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Initialize the recommendation service (it will handle refreshing if needed)
    await recommendation_service.refresh_if_needed()
    
    # Get user interests from the user object
    user_interests = user.get('interests', [])
    
    # Set user location if provided
    user_location = (latitude, longitude) if latitude is not None and longitude is not None else None
    if user_location and not validate_coordinates(latitude, longitude):
        raise HTTPException(status_code=400, detail="Invalid coordinates")
    
    # Get event data
    event_time_str = event.get('start_time')
    event_time = None
    
    # Parse event time similar to how the recommendation service does it
    if event_time_str:
        if isinstance(event_time_str, str):
            try:
                # Try ISO format first
                event_time = datetime.fromisoformat(event_time_str.replace('Z', '+00:00'))
                event_time = event_time.replace(tzinfo=None)  # Make naive
            except ValueError:
                try:
                    # Try other formats
                    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                        try:
                            event_time = datetime.strptime(event_time_str, fmt)
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass
        elif isinstance(event_time_str, (int, float)):
            event_time = datetime.fromtimestamp(event_time_str)
    
    # Calculate component scores
    interest_score = recommendation_service._calculate_interest_score(
        user_interests, 
        event.get('category', [])
    )
    
    social_score = recommendation_service._calculate_social_score(user_id, event_id)
    
    location_score = 0.0
    if user_location:
        venue = event.get('venue', {})
        location_score = recommendation_service._calculate_location_score(user_location, venue)
    
    time_score = 0.0
    if event_time:
        time_score = recommendation_service._calculate_time_relevance_score(event_time)
    
    # Determine if user is new (for weighting)
    is_new_user = user.get('events_attended', 0) < 2 and len(user.get('connections', [])) < 3
    
    # Calculate total score with appropriate weighting
    if is_new_user:
        # New users: focus more on interests and less on social
        total_score = (
            0.5 * interest_score +
            0.1 * social_score +
            0.2 * location_score +
            0.2 * time_score
        )
    else:
        # Regular users: balanced approach
        total_score = (
            0.35 * interest_score +
            0.25 * social_score +
            0.2 * location_score +
            0.2 * time_score
        )
    
    # Replace the current score inflation logic with:
    inflated_score = recommendation_service._inflate_score(total_score)
    
    # Ensure schedule is included in the response (like get_event endpoint)
    if "schedule" not in event:
        event["schedule"] = []
    
    # Ensure image_url is included
    if "image_url" not in event:
        event["image_url"] = None
    
    # Ensure venue with coordinates is included
    if "venue" not in event:
        event["venue"] = {
            "name": None,
            "address": None,
            "latitude": None,
            "longitude": None
        }
    elif isinstance(event["venue"], dict):
        # Ensure venue has all required fields
        if "latitude" not in event["venue"]:
            event["venue"]["latitude"] = None
        if "longitude" not in event["venue"]:
            event["venue"]["longitude"] = None
        if "name" not in event["venue"]:
            event["venue"]["name"] = None
        if "address" not in event["venue"]:
            event["venue"]["address"] = None
            
    # Ensure end_time is included
    if "end_time" not in event:
        # If no end_time, set it to 2 hours after start_time
        if "start_time" in event:
            start_time = event["start_time"]
            if isinstance(start_time, datetime):
                event["end_time"] = start_time + timedelta(hours=2)
            else:
                event["end_time"] = None
        else:
            event["end_time"] = None
            
    # Add score information to the event data
    event["match_score"] = {
        "score": inflated_score,
        "original_score": total_score,
        "breakdown": {
            "interest_score": interest_score,
            "social_score": social_score,
            "location_score": location_score,
            "time_score": time_score
        },
        "matching_interests": list(set(user_interests).intersection(set(event.get('category', [])))),
        "friends_attending": event.get('attendees_count', 0),
        "distance_km": recommendation_service._calculate_distance(
            user_location[0], user_location[1], 
            event.get('venue', {}).get('latitude', 0), 
            event.get('venue', {}).get('longitude', 0)
        ) if user_location and event.get('venue', {}).get('latitude') else None
    }
    
    # Return the full event with added match score information
    return event

# Make sure to export router explicitly
__all__ = ["router"]