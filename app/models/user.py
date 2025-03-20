from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserBase(BaseModel):
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None

class UserCreate(UserBase):
    uid: Optional[str] = None  # Firebase UID

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None

class UserInterests(BaseModel):
    interests: Optional[List[str]] = Field(default=[])

class UserLocation(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class User(UserBase):
    uid: Optional[str] = None
    interests: Optional[List[str]] = []
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    events_attended: Optional[int] = 0
    events_interested: Optional[int] = 0
    connection_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

__all__ = ["UserBase", "UserCreate", "UserUpdate", "UserInterests", "UserLocation", "User"]
