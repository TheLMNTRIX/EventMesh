from fastapi import APIRouter, HTTPException, Query, Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.services.firebase_service import firebase_service

router = APIRouter()

@router.get("/{event_id}/comprehensive")
async def get_comprehensive_event_details(
    event_id: str = Path(..., description="ID of the event to get comprehensive details for")
):
    """
    Get comprehensive details for an event including:
    - Full event information
    - Attendee details with user profiles
    - All feedback and ratings
    
    Returns a single object with all information consolidated.
    """
    # Check if event exists
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get attendees
    attendees = await firebase_service.get_event_attendees(event_id)
    
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
                "email": user_details.get("email"),
                "rsvp_date": attendee.get("rsvp_date")
            }
            enriched_attendees.append(enriched_attendee)
    
    # Get all feedback
    feedback_list = await firebase_service.get_event_feedback(event_id)
    
    # Enrich feedback with user details
    enriched_feedback = []
    for feedback in feedback_list:
        user_id = feedback.get("user_id")
        if user_id:
            user_details = await firebase_service.get_user(user_id)
            if user_details:
                enriched_feedback_item = {
                    **feedback,
                    "user": {
                        "user_id": user_id,
                        "display_name": user_details.get("display_name", "Unknown"),
                        "profile_image_url": user_details.get("profile_image_url")
                    }
                }
                enriched_feedback.append(enriched_feedback_item)
    
    # Calculate feedback stats
    rating_sum = 0
    rating_count = 0
    
    for feedback in feedback_list:
        if feedback.get("rating"):
            rating_sum += feedback["rating"]
            rating_count += 1
    
    avg_rating = rating_sum / rating_count if rating_count > 0 else 0
    
    # Ensure schedule is included in the response
    if "schedule" not in event:
        event["schedule"] = []
    
    # Build the comprehensive response
    comprehensive_details = {
        "event": event,
        "attendees": {
            "count": len(enriched_attendees),
            "list": enriched_attendees
        },
        "feedback": {
            "count": len(enriched_feedback),
            "average_rating": avg_rating,
            "list": enriched_feedback
        }
    }
    
    return comprehensive_details

@router.get("/organizer/{email}")
async def get_organizer_dashboard(
    email: str = Path(..., description="Email of the organizer to fetch events for")
):
    """
    Get summary details for all events organized by a specific email address.
    
    Returns:
    - Total number of events organized
    - Total attendee count across all events
    - Overall average feedback score
    - Average attendance rate per event
    - List of upcoming events sorted by date (nearest first)
    - List of past events sorted by date (most recent first)
    """
    # Get all events (with a high limit to ensure we get all events)
    all_events = await firebase_service.get_events(limit=200)
    
    # Filter events by organizer email
    organizer_events = [
        event for event in all_events 
        if event.get("organizer_email") == email
    ]
    
    if not organizer_events:
        raise HTTPException(status_code=404, detail="No events found for this organizer")
    
    # Calculate total events
    total_events = len(organizer_events)
    
    # Calculate total attendees
    total_attendees = 0
    for event in organizer_events:
        total_attendees += event.get("attendees_count", 0)
    
    # Calculate attendance rate (floor division of total attendees by total events)
    attendance_rate = total_attendees // total_events if total_events > 0 else 0
    
    # Calculate overall feedback score
    total_rating = 0
    total_ratings = 0
    
    for event in organizer_events:
        event_id = event.get("id")
        if event_id:
            feedback_list = await firebase_service.get_event_feedback(event_id)
            for feedback in feedback_list:
                if feedback.get("rating"):
                    total_rating += feedback["rating"]
                    total_ratings += 1
    
    avg_overall_rating = total_rating / total_ratings if total_ratings > 0 else 0
    
    # Create a list of recent/upcoming events sorted by date
    now = datetime.now()
    upcoming_events = []
    past_events = []
    
    for event in organizer_events:
        event_time = event.get("start_time")
        
        # Try to convert the timestamp if it's not already a datetime
        if event_time and not isinstance(event_time, datetime):
            if isinstance(event_time, str):
                try:
                    # Convert to naive datetime by replacing 'Z' and removing timezone info
                    event_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                    # Make naive by removing timezone information
                    event_time = event_time.replace(tzinfo=None)
                except ValueError:
                    try:
                        event_time = datetime.strptime(event_time, "%Y-%m-%dT%H:%M:%S")
                    except ValueError:
                        continue
            elif isinstance(event_time, (int, float)):
                event_time = datetime.fromtimestamp(event_time)
        elif event_time and isinstance(event_time, datetime) and event_time.tzinfo:
            # Make sure timezone-aware datetimes are converted to naive
            event_time = event_time.replace(tzinfo=None)
        
        if event_time:
            simplified_event = {
                "id": event.get("id"),
                "title": event.get("title"),
                "start_time": event.get("start_time"),
                "venue": event.get("venue", {}).get("name"),
                "attendees_count": event.get("attendees_count", 0)
            }
            
            # Now both event_time and now are naive datetimes
            if event_time > now:
                upcoming_events.append(simplified_event)
            else:
                past_events.append(simplified_event)
    
    # Sort upcoming events (soonest first)
    upcoming_events.sort(key=lambda x: x.get("start_time") if isinstance(x.get("start_time"), datetime) 
                        else datetime.min)
    
    # Sort past events (most recent first)
    past_events.sort(key=lambda x: x.get("start_time") if isinstance(x.get("start_time"), datetime) 
                    else datetime.min, reverse=True)
    
    # Build the response with only the requested information
    dashboard_data = {
        "organizer_email": email,
        "stats": {
            "total_events": total_events,
            "total_attendees": total_attendees,
            "average_rating": round(avg_overall_rating, 1),
            "attendance_rate": attendance_rate
        },
        "upcoming_events": upcoming_events,
        "past_events": past_events
    }
    
    return dashboard_data

@router.get("/{event_id}/attendees")
async def get_event_attendees_details(
    event_id: str = Path(..., description="ID of the event to get attendee details for")
):
    """
    Get a simplified list of attendee details for an event including:
    - Name (display_name)
    - Profile picture URL
    - Email
    - RSVP date
    
    Returns an array of attendee objects with the requested fields.
    """
    # Check if event exists
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get attendees
    attendees = await firebase_service.get_event_attendees(event_id)
    
    # Enrich with user details but only include requested fields
    simplified_attendees = []
    for attendee in attendees:
        user_id = attendee["user_id"]
        user_details = await firebase_service.get_user(user_id)
        if user_details:
            simplified_attendee = {
                "display_name": user_details.get("display_name", "Unknown"),
                "profile_image_url": user_details.get("profile_image_url"),
                "email": user_details.get("email"),
                "rsvp_date": attendee.get("rsvp_date")
            }
            simplified_attendees.append(simplified_attendee)
    
    return {
        "event_id": event_id,
        "attendees_count": len(simplified_attendees),
        "attendees": simplified_attendees
    }

@router.get("/{event_id}/feedback")
async def get_event_feedback_with_user_details(
    event_id: str = Path(..., description="ID of the event to get feedback for")
):
    """
    Get all feedback for an event with enriched user information.
    
    Returns:
    - Event ID
    - List of feedback items with user details (display_name, profile image)
    - Overall average rating
    """
    # Check if event exists
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get all feedback for the event
    feedback_list = await firebase_service.get_event_feedback(event_id)
    
    # Calculate feedback stats
    rating_sum = 0
    rating_count = 0
    
    for feedback in feedback_list:
        if feedback.get("rating"):
            rating_sum += feedback["rating"]
            rating_count += 1
    
    avg_rating = rating_sum / rating_count if rating_count > 0 else 0
    
    # Enrich feedback with user details
    enriched_feedback = []
    for feedback in feedback_list:
        user_id = feedback.get("user_id")
        if user_id:
            user_details = await firebase_service.get_user(user_id)
            if user_details:
                enriched_feedback_item = {
                    **feedback,
                    "user": {
                        "user_id": user_id,
                        "display_name": user_details.get("display_name", "Unknown"),
                        "profile_image_url": user_details.get("profile_image_url")
                    }
                }
                enriched_feedback.append(enriched_feedback_item)
    
    return {
        "event_id": event_id,
        "feedback_count": len(enriched_feedback),
        "average_rating": avg_rating,
        "feedback": enriched_feedback
    }

@router.get("/{event_id}/details")
async def get_event_details_with_attendees(
    event_id: str = Path(..., description="ID of the event to get details for")
):
    """
    Get event details by ID with attendee information.
    
    Returns event information in the same structure as the events.py endpoint
    but with additional display_name field for each attendee.
    """
    # Check if event exists
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Ensure schedule is included in the response
    if "schedule" not in event:
        event["schedule"] = []
    
    # Get attendees
    attendees = await firebase_service.get_event_attendees(event_id)
    
    # Enrich attendees with display names
    enriched_attendees = []
    for attendee in attendees:
        user_id = attendee["user_id"]
        user_details = await firebase_service.get_user(user_id)
        
        # Create a copy of the original attendee data
        enriched_attendee = attendee.copy()
        
        # Add the display name if user details were found
        if user_details:
            enriched_attendee["display_name"] = user_details.get("display_name", "Unknown")
        else:
            enriched_attendee["display_name"] = "Unknown"
            
        enriched_attendees.append(enriched_attendee)
    
    # Create a copy of the event to avoid modifying the original
    event_response = event.copy()
    
    # Replace the attendees with our enriched version
    event_response["attendees"] = enriched_attendees
    
    return event_response

__all__ = ["router"]





