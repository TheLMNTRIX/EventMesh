from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class Venue(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

class ScheduleItem(BaseModel):
    title: str
    speaker_name: Optional[str] = None
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime

class EventBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    venue: Optional[Venue] = None
    category: Optional[List[str]] = None
    image_url: Optional[str] = None
    price: Optional[float] = None
    organizer_name: Optional[str] = None
    organizer_id: Optional[str] = None
    organizer_email: Optional[str] = None  # New field
    organizer_phone: Optional[str] = None  # New field
    website_url: Optional[str] = None
    max_attendees: Optional[int] = None
    schedule: Optional[List[ScheduleItem]] = None  # New field for event schedule

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    venue: Optional[Venue] = None
    category: Optional[List[str]] = None
    image_url: Optional[str] = None
    price: Optional[float] = None
    organizer_name: Optional[str] = None
    website_url: Optional[str] = None
    max_attendees: Optional[int] = None

class EventRSVP(BaseModel):
    status: Optional[str] = Field(None, description="One of: attending, interested, declined")

class EventAttendee(BaseModel):
    user_id: Optional[str] = None
    status: Optional[str] = None
    rsvp_date: Optional[datetime] = None

class Event(EventBase):
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    attendees_count: Optional[int] = 0
    attendees: Optional[List[EventAttendee]] = None
    score: Optional[float] = None  # New field for recommendation score
    score_details: Optional[Dict[str, float]] = None  # New field for recommendation score details
    
    class Config:
        from_attributes = True

class EventFilter(BaseModel):
    categories: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_distance_km: Optional[float] = None
    friends_attending: Optional[bool] = None
    free_only: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


__all__ = ["Venue", "EventBase", "EventCreate", "EventUpdate", "EventRSVP", "EventAttendee", "Event", "EventFilter"]