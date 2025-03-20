import os
from typing import Dict, Any
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Load environment variables from .env
load_dotenv()

class Settings(BaseSettings):
    # Firebase configuration
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS", "")
    FIREBASE_WEB_API_KEY: str = os.getenv("FIREBASE_WEB_API_KEY", "")
    FIREBASE_DATABASE_URL: str = os.getenv("FIREBASE_DATABASE_URL", "")
    
    # API settings
    API_DEBUG: bool = os.getenv("API_DEBUG", "False").lower() in ("true", "1", "t")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Event settings
    DEFAULT_EVENT_RADIUS_KM: float = 10.0
    MAX_EVENTS_PER_REQUEST: int = 100
    
    # Recommendation settings
    MIN_MATCH_PERCENTAGE: int = 25
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"  # Allow extra fields from .env
    }

settings = Settings()

# Firebase initialization
cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred, {
    'databaseURL': settings.FIREBASE_DATABASE_URL
})

# Create and export database client
db = firestore.client()
__all__ = ['db', 'settings']
