from geopy.distance import geodesic
from typing import List, Dict, Any, Tuple

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points in kilometers
    """
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers

def filter_events_by_distance(
    events: List[Dict[str, Any]], 
    latitude: float, 
    longitude: float, 
    max_distance_km: float
) -> List[Dict[str, Any]]:
    """
    Filter events that are within the specified distance from the given coordinates
    """
    filtered_events = []
    for event in events:
        venue = event.get('venue', {})
        event_lat = venue.get('latitude')
        event_lon = venue.get('longitude')
        
        if event_lat is not None and event_lon is not None:
            distance = calculate_distance(latitude, longitude, event_lat, event_lon)
            if distance <= max_distance_km:
                event_copy = event.copy()
                event_copy['distance_km'] = round(distance, 2)
                filtered_events.append(event_copy)
    
    return filtered_events

def get_nearby_users(
    users: List[Dict[str, Any]], 
    latitude: float, 
    longitude: float, 
    max_distance_km: float
) -> List[Dict[str, Any]]:
    """
    Find users that are within the specified distance from the given coordinates
    """
    nearby_users = []
    for user in users:
        user_lat = user.get('latitude')
        user_lon = user.get('longitude')
        
        if user_lat is not None and user_lon is not None:
            distance = calculate_distance(latitude, longitude, user_lat, user_lon)
            if distance <= max_distance_km:
                user_copy = user.copy()
                user_copy['distance_km'] = round(distance, 2)
                nearby_users.append(user_copy)
    
    return nearby_users