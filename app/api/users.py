import random
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional
from datetime import datetime

from app.models.user import UserCreate, UserUpdate, User, UserInterests, UserLocation
from app.services.firebase_service import firebase_service

router = APIRouter()

@router.post("/", response_model=User, status_code=201)
async def create_user(user: UserCreate):
    """
    Create a new user account.
    
    Note: Authentication is handled on the mobile client, this endpoint
    creates the user record in our backend after Firebase auth is completed.
    """
    # Generate a 6-digit UID if not provided
    if not user.uid:
        # Generate a random 6-digit number as string
        user.uid = str(random.randint(100000, 999999))
    
    # Check if user already exists
    existing_user = await firebase_service.get_user(user.uid)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Check if email is already in use
    users_ref = firebase_service.db.collection('users')
    email_query = users_ref.where('email', '==', user.email).limit(1)
    if list(email_query.stream()):
        raise HTTPException(status_code=400, detail="Email already in use")
    
    # Prepare user data for storage
    user_data = user.model_dump()
    user_data["created_at"] = datetime.now()
    user_data["interests"] = []
    user_data["events_attended"] = 0
    user_data["events_interested"] = 0
    user_data["connection_count"] = 0
    
    # Create user in database
    created_user = await firebase_service.create_user(user_data)
    return created_user

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user profile by ID"""
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: UserUpdate):
    """Update user profile information"""
    existing_user = await firebase_service.get_user(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Filter out None values
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    
    # Update user
    updated_user = await firebase_service.update_user(user_id, update_data)
    return updated_user

@router.post("/{user_id}/interests", response_model=User)
async def update_user_interests(user_id: str, interests: UserInterests):
    """Update user interests"""
    existing_user = await firebase_service.get_user(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user interests
    updated_user = await firebase_service.update_user(user_id, {"interests": interests.interests})
    return updated_user

@router.post("/{user_id}/location")
async def update_user_location(user_id: str, location: UserLocation):
    """Update user's current location"""
    existing_user = await firebase_service.get_user(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update location
    location_data = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "location_updated_at": datetime.now()
    }
    
    await firebase_service.update_user(user_id, location_data)
    return {"status": "success", "message": "Location updated"}

@router.get("/{user_id}/events")
async def get_user_events(
    user_id: str, 
    status: Optional[str] = Query(None, description="Filter by RSVP status: attending, interested, declined")
):
    """Get events a user has RSVP'd to"""
    existing_user = await firebase_service.get_user(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all events
    all_events = await firebase_service.get_events(limit=200)
    
    user_events = []
    for event in all_events:
        # Check if user is in attendees
        attendees = await firebase_service.get_event_attendees(event["id"])
        user_attendance = next((a for a in attendees if a["user_id"] == user_id), None)
        
        if user_attendance:
            if status is None or user_attendance["status"] == status:
                event_with_status = event.copy()
                event_with_status["user_status"] = user_attendance["status"]
                user_events.append(event_with_status)
    
    return user_events

@router.get("/by-email/{email}")
async def get_user_by_email(email: str):
    """Get user UID by email address"""
    # Search for users with matching email
    users_ref = firebase_service.db.collection('users')
    query = users_ref.where('email', '==', email).limit(1)
    
    users = list(query.stream())
    if not users:
        raise HTTPException(status_code=404, detail="User with this email not found")
    
    user_data = users[0].to_dict()
    return {"uid": user_data.get("uid")}

__all__ = ["router"]