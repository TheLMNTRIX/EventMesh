from typing import List, Dict, Any, Optional
from app.services.firebase_service import firebase_service
from geopy.distance import geodesic
import random
from datetime import datetime, timedelta

class RecommendationService:
    def __init__(self, firebase_service):
        self.firebase_service = firebase_service
    
    async def get_event_recommendations(
        self, 
        user_id: str, 
        latitude: float, 
        longitude: float, 
        max_distance: float = 10.0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get event recommendations for a user based on their interests and location"""
        # Get user data
        user = await self.firebase_service.get_user(user_id)
        if not user or not user.get('interests'):
            return []
        
        user_interests = user.get('interests', [])
        user_location = (latitude, longitude)
        
        # Get events within the date range (today + 30 days)
        today = datetime.now()
        end_date = today + timedelta(days=30)
        
        events = await self.firebase_service.get_events({
            'start_date': today,
            'end_date': end_date
        }, limit=100)  # Get more than needed to filter later
        
        # Calculate match score and distance for each event
        scored_events = []
        for event in events:
            # Calculate interest match percentage
            event_categories = event.get('category', [])
            matching_interests = set(user_interests) & set(event_categories)
            match_percentage = (len(matching_interests) / max(len(user_interests), 1)) * 100
            
            # Calculate distance
            event_location = (event['venue']['latitude'], event['venue']['longitude'])
            distance_km = geodesic(user_location, event_location).kilometers
            
            # Only include events within the specified distance
            if distance_km <= max_distance:
                # Add match percentage and distance to event data
                event_with_score = event.copy()
                event_with_score['match_percentage'] = match_percentage
                event_with_score['distance_km'] = distance_km
                
                # Check if friends are attending
                # (In a real implementation, we'd check connections and their RSVPs)
                connections = await self.firebase_service.get_user_connections(user_id, status='accepted')
                connection_ids = [conn['from_user_id'] if conn['to_user_id'] == user_id else conn['to_user_id'] 
                                 for conn in connections]
                
                attendees = await self.firebase_service.get_event_attendees(event['id'], status='attending')
                attending_connection_ids = [att['user_id'] for att in attendees if att['user_id'] in connection_ids]
                
                event_with_score['connections_attending'] = len(attending_connection_ids)
                event_with_score['connections_attending_ids'] = attending_connection_ids
                
                scored_events.append(event_with_score)
        
        # Sort by match percentage (primary) and distance (secondary)
        scored_events.sort(key=lambda e: (-e['match_percentage'], e['distance_km']))
        
        # Return top recommendations
        return scored_events[:limit]
    
    async def get_connection_recommendations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get connection recommendations based on shared interests and events"""
        # Get user data
        user = await self.firebase_service.get_user(user_id)
        if not user:
            return []
        
        user_interests = user.get('interests', [])
        
        # Get existing connections to exclude them
        existing_connections = await self.firebase_service.get_user_connections(user_id)
        existing_connection_ids = []
        for conn in existing_connections:
            if conn['from_user_id'] == user_id:
                existing_connection_ids.append(conn['to_user_id'])
            else:
                existing_connection_ids.append(conn['from_user_id'])
        
        # Get events user is attending
        user_events = []
        events = await self.firebase_service.get_events(limit=100)
        for event in events:
            attendees = await self.firebase_service.get_event_attendees(event['id'], status='attending')
            if any(att['user_id'] == user_id for att in attendees):
                user_events.append(event)
        
        # Find users with similar interests or attending same events
        potential_connections = {}
        
        # Check users attending the same events
        for event in user_events:
            attendees = await self.firebase_service.get_event_attendees(event['id'], status='attending')
            for attendee in attendees:
                other_user_id = attendee['user_id']
                if other_user_id != user_id and other_user_id not in existing_connection_ids:
                    if other_user_id not in potential_connections:
                        potential_connections[other_user_id] = {
                            'user_id': other_user_id,
                            'common_events': 0,
                            'mutual_interests': [],
                            'mutual_connections': 0
                        }
                    potential_connections[other_user_id]['common_events'] += 1
        
        # Check users with similar interests
        for potential_id in list(potential_connections.keys()):
            other_user = await self.firebase_service.get_user(potential_id)
            if other_user and 'interests' in other_user:
                other_interests = other_user.get('interests', [])
                mutual = set(user_interests) & set(other_interests)
                potential_connections[potential_id]['mutual_interests'] = list(mutual)
            
            # For conversation starters
            if len(potential_connections[potential_id]['mutual_interests']) > 0:
                interests = potential_connections[potential_id]['mutual_interests']
                starters = [
                    f"I see you're also interested in {interests}!",
                    f"What got you into {interests}?",
                    f"Have you been to any great {interests} events lately?"
                ]
                potential_connections[potential_id]['conversation_starters'] = starters[:3]
            else:
                potential_connections[potential_id]['conversation_starters'] = [
                    "Looking forward to the event!",
                    "Have you been to this venue before?",
                    "What other events are you attending soon?"
                ]
        
        # Convert dict to list and sort by relevance
        recommendations = list(potential_connections.values())
        recommendations.sort(key=lambda x: (
            -x['common_events'], 
            -len(x['mutual_interests']),
            -x['mutual_connections']
        ))
        
        # Add display names and profile images
        for rec in recommendations:
            user_data = await self.firebase_service.get_user(rec['user_id'])
            if user_data:
                rec['display_name'] = user_data.get('display_name', 'User')
                rec['profile_image_url'] = user_data.get('profile_image_url')
        
        return recommendations[:limit]

# Initialize service
recommendation_service = RecommendationService(firebase_service)



__all__ = ["recommendation_service"]