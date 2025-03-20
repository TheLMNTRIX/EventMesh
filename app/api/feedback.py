from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional

from app.models.feedback import EventFeedbackCreate, EventFeedbackResponse
from app.services.firebase_service import firebase_service

router = APIRouter()

@router.post("/{event_id}", response_model=EventFeedbackResponse, status_code=201)
async def create_feedback(
    event_id: str = Path(..., description="ID of the event to provide feedback for"),
    user_id: str = Query(..., description="ID of the user providing feedback"),
    feedback: EventFeedbackCreate = ...,
):
    """Create new feedback for an event"""
    # Check if event exists
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create feedback
    feedback_data = feedback.dict()
    created_feedback = await firebase_service.create_event_feedback(event_id, user_id, feedback_data)
    
    return {
        **created_feedback,
        "event_id": event_id,
        "user_id": user_id
    }

@router.get("/{event_id}", response_model=List[EventFeedbackResponse])
async def get_event_feedback(
    event_id: str = Path(..., description="ID of the event to get feedback for"),
):
    """Get all feedback for an event"""
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    feedback_list = await firebase_service.get_event_feedback(event_id)
    return feedback_list

@router.get("/{event_id}/user/{user_id}", response_model=EventFeedbackResponse)
async def get_user_feedback_for_event(
    event_id: str = Path(..., description="ID of the event"),
    user_id: str = Path(..., description="ID of the user"),
):
    """Get a specific user's feedback for an event"""
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get all feedback for the event
    all_feedback = await firebase_service.get_event_feedback(event_id)
    
    # Find the specific user's feedback
    user_feedback = next((f for f in all_feedback if f.get("user_id") == user_id), None)
    if not user_feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return user_feedback

@router.get("/user/{user_id}", response_model=List[EventFeedbackResponse])
async def get_all_user_feedback(
    user_id: str = Path(..., description="ID of the user to get all feedback for"),
):
    """Get all feedback submitted by a user across all events"""
    # Check if user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all events
    events = await firebase_service.get_events(limit=200)
    
    # Collect all feedback from this user across all events
    all_user_feedback = []
    for event in events:
        event_id = event["id"]
        # Get feedback for this event
        event_feedback = await firebase_service.get_event_feedback(event_id)
        # Find this user's feedback if it exists
        user_feedback = next((f for f in event_feedback if f.get("user_id") == user_id), None)
        if user_feedback:
            # Add event_id to the feedback object if not present
            if "event_id" not in user_feedback:
                user_feedback["event_id"] = event_id
            all_user_feedback.append(user_feedback)
    
    return all_user_feedback

@router.put("/{event_id}/user/{user_id}", response_model=EventFeedbackResponse)
async def update_feedback(
    event_id: str = Path(..., description="ID of the event"),
    user_id: str = Path(..., description="ID of the user"),
    feedback: EventFeedbackCreate = ...,
):
    """Update a user's feedback for an event"""
    # Check if event exists
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if feedback exists
    all_feedback = await firebase_service.get_event_feedback(event_id)
    existing_feedback = next((f for f in all_feedback if f.get("user_id") == user_id), None)
    if not existing_feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    # Update feedback
    feedback_data = feedback.dict()
    updated_feedback = await firebase_service.create_event_feedback(event_id, user_id, feedback_data)
    
    return {
        **updated_feedback,
        "event_id": event_id,
        "user_id": user_id
    }

@router.delete("/{event_id}/user/{user_id}")
async def delete_feedback(
    event_id: str = Path(..., description="ID of the event"),
    user_id: str = Path(..., description="ID of the user"),
):
    """Delete a user's feedback for an event"""
    # Check if event exists
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Add implementation to delete feedback
    # Note: You'll need to add a delete_event_feedback method to your firebase_service
    success = await firebase_service.delete_event_feedback(event_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feedback not found or could not be deleted")
    
    return {"status": "success", "message": "Feedback deleted successfully"}




__all__ = [
    "router",
]