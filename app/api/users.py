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
    
    # Check if email is already in use
    users_ref = firebase_service.db.collection('users')
    email_query = users_ref.where('email', '==', user.email)
    existing_users = list(email_query.stream())
    
    # Function to check if a UID is a 6-digit number
    def is_six_digit_uid(uid):
        return uid and uid.isdigit() and len(uid) == 6
    
    # Check if there's a user with same email but non-6-digit UID (Firebase UUID)
    firebase_user_doc = None
    for doc in existing_users:
        user_data = doc.to_dict()
        if not is_six_digit_uid(user_data.get('uid')):
            firebase_user_doc = doc
            break
    
    # If found, delete the document with Firebase UUID
    if firebase_user_doc:
        print(f"Found existing user with Firebase UUID: {firebase_user_doc.id}")
        print(f"Deleting document to replace with 6-digit UID user: {user.uid}")
        
        # Copy any important data before deleting
        existing_data = firebase_user_doc.to_dict()
        saved_interests = existing_data.get('interests', [])
        saved_events_attended = existing_data.get('events_attended', 0)
        saved_connection_count = existing_data.get('connection_count', 0)
        saved_profile_image = existing_data.get('profile_image_url')
        saved_bio = existing_data.get('bio')
        
        # Delete the document
        firebase_user_doc.reference.delete()
        print(f"Deleted document with Firebase UUID: {firebase_user_doc.id}")
        
        # Preserve important user data
        if saved_interests:
            user_data["interests"] = saved_interests
        if saved_profile_image and not user.profile_image_url:
            user.profile_image_url = saved_profile_image
        if saved_bio and not user.bio:
            user.bio = saved_bio
    
    # Check if a user with our 6-digit UID already exists
    existing_user = await firebase_service.get_user(user.uid)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this UID already exists")
    
    # Prepare user data for storage
    user_data = user.model_dump()
    user_data["created_at"] = datetime.now()
    
    # Initialize with empty arrays/zeros if not preserved from previous document
    if "interests" not in user_data:
        user_data["interests"] = []
    if "events_attended" not in user_data:
        user_data["events_attended"] = 0
    if "events_interested" not in user_data:
        user_data["events_interested"] = 0
    if "connection_count" not in user_data:
        user_data["connection_count"] = 0
    
    # Create user in database
    created_user = await firebase_service.create_user(user_data)
    
    print(f"Created new user with 6-digit UID: {user.uid}")
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
            # We only support "attending" status now, so no need to check status
            if status is None or status == "attending":
                event_with_status = event.copy()
                event_with_status["user_status"] = "attending"  # Hardcode to "attending" as that's the only status now
                
                # Ensure schedule is included
                if "schedule" not in event_with_status:
                    event_with_status["schedule"] = []
                    
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