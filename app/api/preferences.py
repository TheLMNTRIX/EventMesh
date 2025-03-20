from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.firebase_service import firebase_service

router = APIRouter()

@router.get("/{user_id}")
async def get_user_preferences(user_id: str):
    """Get user preferences"""
    # Check if user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Extract preferences from user data
    preferences = {
        "interests": user.get("interests", []),
        "notification_settings": user.get("notification_settings", {
            "event_reminders": True,
            "friend_activity": True,
            "nearby_events": True,
            "recommendations": True
        }),
        "privacy_settings": user.get("privacy_settings", {
            "profile_visibility": "public",
            "location_sharing": "friends",
            "allow_messages": "everyone"
        }),
        "calendar_integration": user.get("calendar_integration", False),
        "recommendation_preferences": user.get("recommendation_preferences", {
            "max_distance_km": 20,
            "include_free_only": False,
            "include_friends_attending": True,
            "preferred_days": ["weekend", "weekday_evening"]
        })
    }
    
    return preferences

@router.put("/{user_id}/notification_settings")
async def update_notification_settings(user_id: str, settings: Dict[str, bool]):
    """Update user notification settings"""
    # Check if user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate settings
    valid_keys = ["event_reminders", "friend_activity", "nearby_events", "recommendations"]
    for key in settings:
        if key not in valid_keys:
            raise HTTPException(status_code=400, detail=f"Invalid notification setting: {key}")
    
    # Get existing settings or initialize defaults
    notification_settings = user.get("notification_settings", {
        "event_reminders": True,
        "friend_activity": True,
        "nearby_events": True,
        "recommendations": True
    })
    
    # Update with new settings
    notification_settings.update(settings)
    
    # Save to database
    await firebase_service.update_user(user_id, {"notification_settings": notification_settings})
    
    return {
        "status": "success",
        "message": "Notification settings updated",
        "notification_settings": notification_settings
    }

@router.put("/{user_id}/privacy_settings")
async def update_privacy_settings(user_id: str, settings: Dict[str, str]):
    """Update user privacy settings"""
    # Check if user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate settings
    valid_keys = ["profile_visibility", "location_sharing", "allow_messages"]
    valid_values = {
        "profile_visibility": ["public", "connections", "private"],
        "location_sharing": ["everyone", "friends", "none"],
        "allow_messages": ["everyone", "connections", "none"]
    }
    
    for key, value in settings.items():
        if key not in valid_keys:
            raise HTTPException(status_code=400, detail=f"Invalid privacy setting: {key}")
        if key in valid_values and value not in valid_values[key]:
            raise HTTPException(status_code=400, detail=f"Invalid value for {key}: {value}")
    
    # Get existing settings or initialize defaults
    privacy_settings = user.get("privacy_settings", {
        "profile_visibility": "public",
        "location_sharing": "friends",
        "allow_messages": "everyone"
    })
    
    # Update with new settings
    privacy_settings.update(settings)
    
    # Save to database
    await firebase_service.update_user(user_id, {"privacy_settings": privacy_settings})
    
    return {
        "status": "success",
        "message": "Privacy settings updated",
        "privacy_settings": privacy_settings
    }

@router.put("/{user_id}/calendar_integration")
async def update_calendar_integration(user_id: str, enabled: bool):
    """Enable or disable calendar integration"""
    # Check if user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update calendar integration setting
    await firebase_service.update_user(user_id, {"calendar_integration": enabled})
    
    return {
        "status": "success",
        "message": f"Calendar integration {'enabled' if enabled else 'disabled'}",
        "calendar_integration": enabled
    }

@router.put("/{user_id}/recommendation_preferences")
async def update_recommendation_preferences(user_id: str, preferences: Dict[str, Any]):
    """Update recommendation preferences"""
    # Check if user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate preferences
    valid_keys = ["max_distance_km", "include_free_only", "include_friends_attending", "preferred_days"]
    
    for key in preferences:
        if key not in valid_keys:
            raise HTTPException(status_code=400, detail=f"Invalid recommendation preference: {key}")
    
    # Type validation
    if "max_distance_km" in preferences and not isinstance(preferences["max_distance_km"], (int, float)):
        raise HTTPException(status_code=400, detail="max_distance_km must be a number")
    
    if "include_free_only" in preferences and not isinstance(preferences["include_free_only"], bool):
        raise HTTPException(status_code=400, detail="include_free_only must be a boolean")
    
    if "include_friends_attending" in preferences and not isinstance(preferences["include_friends_attending"], bool):
        raise HTTPException(status_code=400, detail="include_friends_attending must be a boolean")
    
    if "preferred_days" in preferences:
        valid_days = ["weekend", "weekday", "weekday_evening", "weekday_morning"]
        if not isinstance(preferences["preferred_days"], list):
            raise HTTPException(status_code=400, detail="preferred_days must be a list")
        for day in preferences["preferred_days"]:
            if day not in valid_days:
                raise HTTPException(status_code=400, detail=f"Invalid preferred day: {day}")
    
    # Get existing preferences or initialize defaults
    recommendation_preferences = user.get("recommendation_preferences", {
        "max_distance_km": 20,
        "include_free_only": False,
        "include_friends_attending": True,
        "preferred_days": ["weekend", "weekday_evening"]
    })
    
    # Update with new preferences
    recommendation_preferences.update(preferences)
    
    # Save to database
    await firebase_service.update_user(user_id, {"recommendation_preferences": recommendation_preferences})
    
    return {
        "status": "success",
        "message": "Recommendation preferences updated",
        "recommendation_preferences": recommendation_preferences
    }