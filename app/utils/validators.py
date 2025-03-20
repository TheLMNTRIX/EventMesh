from datetime import datetime
from typing import List, Dict, Any, Optional

def validate_event_dates(start_time: datetime, end_time: datetime) -> bool:
    """
    Validate that event end time is after start time
    """
    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
        return False
    
    return end_time > start_time

def validate_coordinates(latitude: float, longitude: float) -> bool:
    """
    Validate geographic coordinates
    """
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return False
    
    if latitude < -90 or latitude > 90:
        return False
    
    if longitude < -180 or longitude > 180:
        return False
    
    return True

def validate_rating(rating: int) -> bool:
    """
    Validate event rating (1-5 stars)
    """
    if not isinstance(rating, int):
        return False
    
    return 1 <= rating <= 5

def validate_rsvp_status(status: str) -> bool:
    """
    Validate RSVP status
    """
    valid_statuses = ['attending', 'interested', 'declined']
    return status in valid_statuses

def validate_connection_status(status: str) -> bool:
    """
    Validate connection status
    """
    valid_statuses = ['pending', 'accepted', 'declined', 'blocked']
    return status in valid_statuses