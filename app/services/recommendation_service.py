import networkx as nx
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Set
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
import time
import random
from firebase_admin import firestore

class RecommendationService:
    def __init__(self):
        self.db = firestore.client()
        self.users_data = {}  
        self.events_data = {}  
        self.social_graph = None
        self.last_refresh_time = 0
        self.refresh_interval = 3600  # Refresh cache every hour
        
    async def initialize(self):
        """Initialize the recommendation engine"""
        await self._load_all_data()
        self._build_social_graph()
        self.last_refresh_time = time.time()

    async def refresh_if_needed(self):
        """Refresh data if the refresh interval has passed"""
        current_time = time.time()
        if current_time - self.last_refresh_time > self.refresh_interval:
            await self.initialize()

    async def _load_all_data(self):
        """Load all users and events data at once"""
        # Get all users in a single batch
        users_ref = self.db.collection('users').stream()
        self.users_data = {user.id: user.to_dict() for user in users_ref}
        
        # Get all events in a single batch
        events_ref = self.db.collection('events').stream()
        self.events_data = {event.id: event.to_dict() for event in events_ref}
    
    def _build_social_graph(self):
        """Create a social graph from user connections"""
        G = nx.Graph()
        
        # Add all nodes with their interests
        for user_id, user_data in self.users_data.items():
            G.add_node(user_id, interests=set(user_data.get('interests', [])))
        
        # Add all edges (connections)
        for user_id, user_data in self.users_data.items():
            for connection_id in user_data.get('connections', []):
                if connection_id in G:
                    G.add_edge(user_id, connection_id)
        
        self.social_graph = G

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula (in km)"""
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        radius = 6378  # Radius of Earth in kilometers
        distance = radius * c
        
        return distance

    def _calculate_interest_score(self, user_interests: List[str], event_categories: List[str]) -> float:
        """Calculate interest match score based on common categories"""
        if not user_interests or not event_categories:
            return 0.0
        
        # Simple direct matching
        user_interests_set = set(user_interests)
        event_categories_set = set(event_categories)
        common_categories = user_interests_set.intersection(event_categories_set)
        
        # Return the fraction of event categories that match user interests
        return len(common_categories) / len(event_categories_set) if event_categories_set else 0.0

    def _calculate_social_score(self, user_id: str, event_id: str) -> float:
        """Calculate social score based on friends attending the event"""
        if user_id not in self.social_graph or event_id not in self.events_data:
            return 0.0
            
        event = self.events_data[event_id]
        event_attendees = set()
        
        # Get attendees from the event data
        for attendee in event.get('attendees', []):
            if isinstance(attendee, dict):
                attendee_id = attendee.get('user_id')
                if attendee_id:
                    event_attendees.add(attendee_id)
            elif isinstance(attendee, str):
                event_attendees.add(attendee)
        
        # Get user's connections
        user_connections = set(self.social_graph.neighbors(user_id))
        
        # Calculate how many connections are attending
        attending_connections = user_connections.intersection(event_attendees)
        
        # Return score based on percentage of connections attending
        return len(attending_connections) / len(user_connections) if user_connections else 0.0
    
    def _inflate_score(self, score: float) -> float:
        """Apply consistent score inflation to recommendation scores
        
        Uses a gradient approach:
        - For scores <= 0.5: add flat 0.25 inflation
        - For scores between 0.5 and 0.9: use linear gradient (0.25 to 0)
        - Cap at 0.9
        """
        if score <= 0.5:
            # For scores below 50%, add a flat 0.25 (25%)
            inflated_score = score + 0.25
        else:
            # For scores between 50% and 90%, use a linear gradient
            max_score = 0.9
            min_score = 0.5
            max_inflation = 0.25
            min_inflation = 0.0
            
            # Calculate where the score falls in the 50%-90% range
            score_position = (score - min_score) / (max_score - min_score)
            
            # Calculate inflation based on position
            inflation = max_inflation - score_position * (max_inflation - min_inflation)
            
            # Apply the calculated inflation
            inflated_score = score + inflation
            
        # Safety cap at 90%
        return min(0.9, inflated_score)

    def _calculate_location_score(self, user_location: Tuple[float, float], event_location: Dict[str, float], max_distance: float = 20.0) -> float:
        """Calculate location score based on proximity"""
        if not user_location or not event_location:
            return 0.0
            
        event_lat = event_location.get('latitude')
        event_lon = event_location.get('longitude')
        
        if event_lat is None or event_lon is None:
            return 0.0
            
        # Calculate distance
        distance = self._calculate_distance(
            user_location[0], user_location[1],
            event_lat, event_lon
        )
        
        # Convert to score (closer is better)
        return max(0.0, 1.0 - (distance / max_distance))

    def _calculate_time_relevance_score(self, event_time: datetime) -> float:
        """Calculate time relevance score (events coming soon get higher scores)"""
        if not event_time:
            return 0.0
            
        now = datetime.now()
        
        # Ensure event_time is naive if it has timezone info
        if hasattr(event_time, 'tzinfo') and event_time.tzinfo is not None:
            event_time = event_time.replace(tzinfo=None)
        
        # If event is in the past, score is 0
        if event_time < now:
            return 0.0
            
        # Score decreases as event gets further in the future
        days_until_event = (event_time - now).days
        
        # Events within the next 14 days get higher scores
        if days_until_event <= 14:
            return 1.0 - (days_until_event / 14)
        # Events within the next 30 days get medium scores
        elif days_until_event <= 30:
            return 0.5 - ((days_until_event - 14) / 30)
        else:
            return 0.3  # Baseline score for future events
    
    def _get_conversation_starters(self, user_interests: List[str], connection_interests: List[str]) -> List[str]:
        """Generate conversation starter ideas based on common interests"""
        common_interests = set(user_interests).intersection(set(connection_interests))
        
        conversation_starters = []
        interest_prompts = {
            "tech": ["What tech are you working with these days?", "Any new gadgets you're excited about?"],
            "music": ["Heard any good music lately?", "What concerts are you looking forward to?"],
            "art": ["Been to any good exhibitions recently?", "What kind of art inspires you?"],
            "food": ["Any restaurant recommendations?", "What's your favorite cuisine?"],
            "sports": ["Been following any games lately?", "Do you play any sports?"],
            "gaming": ["What games are you playing these days?", "PC or console gamer?"],
            "photography": ["What do you like to photograph?", "What camera do you use?"],
            "fashion": ["Any fashion trends you're into right now?", "Where do you shop for clothes?"],
            "literature": ["Read any good books lately?", "Who's your favorite author?"],
            "science": ["Any cool scientific breakthroughs you're excited about?", "What area of science interests you most?"],
            "movies": ["Seen any good movies lately?", "What's your favorite genre?"],
            "travel": ["What's your favorite place you've traveled to?", "Where are you planning to go next?"],
            "fitness": ["What's your workout routine like?", "Any fitness goals you're working on?"],
            "business": ["Any interesting startups you've heard of lately?", "What industry are you in?"],
            "education": ["Learning anything new these days?", "What subject do you find most interesting?"]
        }
        
        for interest in common_interests:
            if interest in interest_prompts:
                conversation_starters.append(random.choice(interest_prompts[interest]))
                
            if len(conversation_starters) >= 3:
                break
                
        if not conversation_starters and common_interests:
            # Generic fallback based on common interests
            interest = random.choice(list(common_interests))
            conversation_starters.append(f"I see you're also interested in {interest}. What aspects of it do you enjoy?")
            
        return conversation_starters
    
    async def get_event_recommendations(self, user_id: str, latitude: float = None, longitude: float = None, 
                                       max_distance_km: float = 10.0, limit: int = 10) -> List[Dict[str, Any]]:
        """Get event recommendations for a user"""
        await self.refresh_if_needed()
        
        # Get user data
        user = self.users_data.get(user_id)
        if not user:
            return []
            
        user_interests = user.get('interests', [])
        user_location = (latitude, longitude) if latitude is not None and longitude is not None else None
        
        # Get user's connections
        user_connections = user.get('connections', [])
        if isinstance(user_connections, int):
            user_connections = []
        user_connections = set(user_connections)
        
        # Determine if this is a new user
        is_new_user = user.get('events_attended', 0) < 2 and len(user_connections) < 3
        
        # Filter events
        recommended_events = []
        now = datetime.now().replace(tzinfo=None)  # Ensure now is always naive
        
        for event_id, event in self.events_data.items():
            try:
                # Skip past events
                event_time_str = event.get('start_time')
                if not event_time_str:
                    continue
                    
                # Convert string to datetime if needed
                event_time = event_time_str
                
                # Handle different datetime formats and types
                if isinstance(event_time_str, str):
                    try:
                        # Try ISO format first with timezone handling
                        event_time = datetime.fromisoformat(event_time_str.replace('Z', '+00:00'))
                    except ValueError:
                        try:
                            # Try other common datetime string formats
                            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                                try:
                                    event_time = datetime.strptime(event_time_str, fmt)
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            # If all parsing fails, skip this event
                            continue
                            
                # Handle timestamp (integer or float)
                elif isinstance(event_time, (int, float)):
                    event_time = datetime.fromtimestamp(event_time)
                    
                # Always ensure the datetime is naive by removing timezone
                if hasattr(event_time, 'tzinfo') and event_time.tzinfo is not None:
                    event_time = event_time.replace(tzinfo=None)
                    
                # Now both datetimes are naive, so comparison should work
                if event_time < now:
                    continue
                    
                # Rest of your code stays the same...
                interest_score = self._calculate_interest_score(
                    user_interests, 
                    event.get('category', [])
                )
                
                social_score = self._calculate_social_score(user_id, event_id)
                
                location_score = 0.0
                if user_location:
                    venue = event.get('venue', {})
                    location_score = self._calculate_location_score(user_location, venue, max_distance_km)
                    
                time_score = self._calculate_time_relevance_score(event_time)
                
                # Skip events that are too far away
                if location_score == 0.0 and user_location:
                    continue
                    
                # Calculate total score with different weights
                if is_new_user:
                    # New users: focus more on interests and less on social
                    total_score = (
                        0.5 * interest_score +
                        0.1 * social_score +
                        0.2 * location_score +
                        0.2 * time_score
                    )
                else:
                    # Regular users: balanced approach
                    total_score = (
                        0.35 * interest_score +
                        0.25 * social_score +
                        0.2 * location_score +
                        0.2 * time_score
                    )
                
                # Apply score inflation
                inflated_score = self._inflate_score(total_score)
                
                # Check if event attendees exists and initialize it if not
                if 'attendees' not in event:
                    event['attendees'] = []
                    
                # Format venue correctly if missing
                if 'venue' not in event:
                    event['venue'] = {
                        'name': None,
                        'address': None,
                        'latitude': None,
                        'longitude': None
                    }
                    
                # Ensure schedule is included
                if 'schedule' not in event:
                    event['schedule'] = []
                    
                recommended_events.append({
                    'id': event_id,
                    'title': event.get('title', 'Untitled Event'),
                    'description': event.get('description', ''),
                    'start_time': event_time,
                    'image_url': event.get('image_url'),
                    'venue': event.get('venue', {}),
                    'category': event.get('category', []),
                    'price': event.get('price', 0),
                    'attendees_count': event.get('attendees_count', 0),
                    'attendees': event.get('attendees', []),
                    'schedule': event.get('schedule', []),
                    'score': inflated_score,
                    'original_score': total_score,
                    'score_details': {
                        'interest_score': interest_score,
                        'social_score': social_score,
                        'location_score': location_score,
                        'time_score': time_score
                    }
                })
            except Exception as e:
                # Skip this event if any errors occur during processing
                # print(f"Error processing event {event_id}: {str(e)}")
                continue
                
        # Sort by score and limit results
        recommended_events.sort(key=lambda x: x['score'], reverse=True)
        return recommended_events[:limit]
        
    async def get_connection_recommendations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get connection recommendations for a user"""
        await self.refresh_if_needed()
        
        # Get user data
        user = self.users_data.get(user_id)
        if not user:
            return []
            
        user_interests = user.get('interests', [])
        
        # Get user's existing connections
        user_connections = set(user.get('connections', []))
        
        # Find potential connections
        potential_connections = []
        
        for other_id, other_user in self.users_data.items():
            # Skip if this is the same user or already connected
            if other_id == user_id or other_id in user_connections:
                continue
                
            other_interests = other_user.get('interests', [])
            
            # Calculate interest similarity
            common_interests = set(user_interests).intersection(set(other_interests))
            interest_score = len(common_interests) / max(len(user_interests), 1) if user_interests else 0
            
            # Calculate mutual connections (people they both know)
            mutual_connections = []
            if self.social_graph and user_id in self.social_graph and other_id in self.social_graph:
                user_friends = set(self.social_graph.neighbors(user_id))
                other_friends = set(self.social_graph.neighbors(other_id))
                mutual_connections = list(user_friends.intersection(other_friends))
                
            mutual_connections_score = len(mutual_connections) / 10  # Cap at 10 mutual connections
            
            # Calculate common events attended
            user_events = self._get_user_events(user_id)
            other_events = self._get_user_events(other_id)
            common_events = len(user_events.intersection(other_events))
            common_events_score = min(1.0, common_events / 5)  # Cap at 5 common events
            
            # Calculate total score
            total_score = (
                0.5 * interest_score +
                0.3 * mutual_connections_score +
                0.2 * common_events_score
            )
            
            # Apply score inflation
            inflated_score = self._inflate_score(total_score)
            
            # Generate conversation starters
            conversation_starters = self._get_conversation_starters(user_interests, other_interests)
            
            potential_connections.append({
                'connection_id': other_id,
                'display_name': other_user.get('display_name', 'Unknown User'),
                'profile_image_url': other_user.get('profile_image_url'),
                'bio': other_user.get('bio', ''),
                'mutual_interests': list(common_interests),
                'mutual_connections': len(mutual_connections),
                'events_in_common': common_events,
                'conversation_starters': conversation_starters,
                'score': inflated_score,
                'original_score': total_score
            })
            
        # Sort by score and limit results
        potential_connections.sort(key=lambda x: x['score'], reverse=True)
        return potential_connections[:limit]
        
    def _get_user_events(self, user_id: str) -> Set[str]:
        """Get set of events a user has attended"""
        attended_events = set()
        
        for event_id, event in self.events_data.items():
            # Check attendees list
            attendees = event.get('attendees', [])
            
            # Handle different attendee formats
            for attendee in attendees:
                attendee_id = None
                if isinstance(attendee, dict):
                    attendee_id = attendee.get('user_id')
                elif isinstance(attendee, str):
                    attendee_id = attendee
                    
                if attendee_id == user_id:
                    attended_events.add(event_id)
                    break
                    
        return attended_events
        
    async def get_event_based_connection_recommendations(self, event_id: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get connection recommendations for a user at a specific event"""
        await self.refresh_if_needed()
        
        # Get event data
        event = self.events_data.get(event_id)
        if not event:
            return []
            
        # Get user data
        user = self.users_data.get(user_id)
        if not user:
            return []
            
        user_interests = user.get('interests', [])
        user_connections = set(user.get('connections', []))
        
        # Get event attendees
        attendees = []
        for attendee in event.get('attendees', []):
            if isinstance(attendee, dict):
                attendee_id = attendee.get('user_id')
                if attendee_id and attendee_id != user_id and attendee_id not in user_connections:
                    attendees.append(attendee_id)
            elif isinstance(attendee, str) and attendee != user_id and attendee not in user_connections:
                attendees.append(attendee)
                
        # Calculate recommendations based on event attendees
        recommendations = []
        for attendee_id in attendees:
            attendee = self.users_data.get(attendee_id)
            if not attendee:
                continue
                
            attendee_interests = attendee.get('interests', [])
            
            # Calculate interest overlap
            common_interests = set(user_interests).intersection(set(attendee_interests))
            interest_score = len(common_interests) / max(len(user_interests), 1) if user_interests else 0
            
            # Find mutual connections
            mutual_connections = []
            if self.social_graph and user_id in self.social_graph and attendee_id in self.social_graph:
                user_friends = set(self.social_graph.neighbors(user_id))
                attendee_friends = set(self.social_graph.neighbors(attendee_id))
                mutual_connections = list(user_friends.intersection(attendee_friends))
                
            mutual_score = min(1.0, len(mutual_connections) / 5)  # Cap at 5 mutual connections
            
            # Generate conversation starters related to the event
            event_category = event.get('category', [])
            event_title = event.get('title', '')
            
            # Get common interests related to the event
            event_related_interests = set(event_category).intersection(set(common_interests))
            
            conversation_starters = []
            if event_related_interests:
                interest = random.choice(list(event_related_interests))
                conversation_starters.append(f"I see you're also interested in {interest}. What brought you to this event?")
            else:
                conversation_starters.append(f"What are you most looking forward to at {event_title}?")
                
            # Calculate total score
            total_score = 0.7 * interest_score + 0.3 * mutual_score
            
            # Apply score inflation
            inflated_score = self._inflate_score(total_score)
            
            recommendations.append({
                'connection_id': attendee_id,
                'display_name': attendee.get('display_name', 'Unknown User'),
                'profile_image_url': attendee.get('profile_image_url'),
                'bio': attendee.get('bio', ''),
                'mutual_interests': list(common_interests),
                'mutual_connections': len(mutual_connections),
                'conversation_starters': conversation_starters,
                'score': inflated_score,
                'original_score': total_score
            })
            
        # Sort by score and limit results
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]

# Initialize the recommendation service
recommendation_service = RecommendationService()