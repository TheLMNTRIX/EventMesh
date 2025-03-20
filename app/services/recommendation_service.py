import networkx as nx
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
import time

class RecommendationEngine:
    def __init__(self, db):
        self.db = db
        self.users_data = {}  
        self.events_data = {}  
        self.social_graph = None
        self.user_item_matrix = None
        self.user_map = {}
        self.event_map = {}
        self.svd_u = None
        self.svd_sigma = None
        self.svd_vt = None
        self.last_refresh_time = 0
        self.refresh_interval = 3600
        
    def initialize(self):
        """Initialize the recommendation engine"""
        self._load_all_data()
        self._build_social_graph()
        self._build_user_item_matrix()
        self._compute_svd()
        self.last_refresh_time = time.time()

    def refresh_if_needed(self):
        """Refresh data if the refresh interval has passed"""
        current_time = time.time()
        if current_time - self.last_refresh_time > self.refresh_interval:
            self.initialize()

    def _load_all_data(self):
        """Load all users and events data at once"""
        # Get all users in a single batch
        users_ref = self.db.collection('users').stream()
        self.users_data = {user.id: user.to_dict() for user in users_ref}
        
        # Get all events in a single batch
        events_ref = self.db.collection('events').stream()
        self.events_data = {event.id: event.to_dict() for event in events_ref}
        
        # Create mappings for matrix operations
        self.user_map = {user_id: i for i, user_id in enumerate(self.users_data.keys())}
        self.event_map = {event_id: i for i, event_id in enumerate(self.events_data.keys())}
    
    def _build_social_graph(self):
        """Create a social graph from cached user connections"""
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

    def _build_user_item_matrix(self):
        """Create a sparse user-item matrix for collaborative filtering from cached data"""
        data = []
        row_ind = []
        col_ind = []
        
        # Loop through events to get attendance data
        for event_id, event_data in self.events_data.items():
            for attendee_id in event_data.get('attendees', []):
                if attendee_id in self.user_map and event_id in self.event_map:
                    row_ind.append(self.user_map[attendee_id])
                    col_ind.append(self.event_map[event_id])
                    data.append(1)  # Binary attendance
        
        self.user_item_matrix = csr_matrix(
            (data, (row_ind, col_ind)), 
            shape=(len(self.users_data), len(self.events_data))
        )

    def _compute_svd(self):
        """Compute SVD for collaborative filtering"""
        if min(self.user_item_matrix.shape) > 1:
            k = min(10, min(self.user_item_matrix.shape) - 1)
            self.svd_u, self.svd_sigma, self.svd_vt = svds(self.user_item_matrix.tocsc(), k=k)

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
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

    def _calculate_interest_score(self, user_interests, event_categories):
        """Calculate direct interest match score based on common categories"""
        if not user_interests or not event_categories:
            return 0.0
        
        # Simple direct matching
        user_interests_set = set(user_interests)
        event_categories_set = set(event_categories)
        common_categories = user_interests_set.intersection(event_categories_set)
        
        # Return the fraction of event categories that match user interests
        return len(common_categories) / len(event_categories_set) if event_categories_set else 0.0

    def _calculate_social_influence_score(self, user_id, event_categories):
        """Calculate social influence score based on connections' interests"""
        if user_id not in self.social_graph:
            return 0.0
        
        connections = list(self.social_graph.neighbors(user_id))
        if not connections:
            return 0.0
        
        connection_scores = []
        for connection_id in connections:
            connection_interests = self.social_graph.nodes[connection_id].get('interests', set())
            common_tags = connection_interests.intersection(set(event_categories))
            connection_scores.append(len(common_tags) / len(event_categories) if event_categories else 0)
        
        # Calculate both average and majority influence
        avg_score = sum(connection_scores) / len(connection_scores)
        majority_score = sum(1 for score in connection_scores if score > 0.5) / len(connection_scores)
        
        return 0.7 * avg_score + 0.3 * majority_score

    def _calculate_collaborative_filtering_score(self, user_id, event_id):
        """Calculate collaborative filtering score using SVD"""
        if self.svd_u is None or user_id not in self.user_map or event_id not in self.event_map:
            return 0.0
            
        user_idx = self.user_map[user_id]
        event_idx = self.event_map[event_id]
        
        user_factors = self.svd_u[user_idx, :]
        item_factors = self.svd_vt[:, event_idx]
        
        predicted_rating = np.dot(np.dot(user_factors, np.diag(self.svd_sigma)), item_factors)
        return float(predicted_rating)

    def _calculate_distance_score(self, user_location, venue_location, max_distance=50.0):
        """Calculate score based on distance (closer is better)"""
        if not user_location or not venue_location:
            return 0.5  # Neutral score if locations aren't available
        
        distance = self._calculate_distance(
            user_location[0], user_location[1],
            venue_location["latitude"], venue_location["longitude"]
        )
        
        # Convert distance to a score (closer is better)
        distance_score = max(0, 1.0 - (distance / max_distance))
        return distance_score

    def _calculate_enhanced_interest_score(self, user_interests, event):
        """Calculate enhanced interest score using categories and description"""
        interest_score = self._calculate_interest_score(
            user_interests, 
            event.get("category", [])
        )
        
        # Additional explicit text matching in title and description
        title = event.get("title", "").lower()
        description = event.get("description", "").lower()
        
        # Check for interests mentioned in description or title
        for interest in user_interests:
            interest_lower = interest.lower()
            if interest_lower in description or interest_lower in title:
                interest_score += 0.1  # Boost score if interests are mentioned
        
        return min(1.0, interest_score)  # Cap at 1.0

    def _calculate_popularity_score(self, event):
        """Calculate popularity based on attendee count"""
        attendees_count = event.get("attendees_count", 0)
        return min(1.0, attendees_count / 50)

    def get_recommendations(self, user_id, num_recommendations=5, user_location=None):
        """Get event recommendations for a user using cached data"""
        self.refresh_if_needed()
        
        if user_location is None:
            user_location = (37.7749, -122.4194)  # San Francisco coordinates
        
        # Get user data from cache
        if user_id not in self.users_data:
            return []
        
        user_data = self.users_data[user_id]
        user_interests = user_data.get('interests', [])
        is_new_user = len(user_data.get('connections', [])) == 0 and user_data.get('events_attended', 0) == 0
        
        # Filter out events the user has already attended
        attended_events = set()
        for event_id, event_data in self.events_data.items():
            if user_id in event_data.get('attendees', []):
                attended_events.add(event_id)
        
        # Filter to future events only
        now = datetime.now().timestamp()
        future_events = []
        for event_id, event_data in self.events_data.items():
            if (event_id not in attended_events and 
                event_data.get("start_time", 0) > now):
                # Add ID to the event data for reference
                event_data_with_id = {"id": event_id, **event_data}
                future_events.append(event_data_with_id)
        
        # Calculate scores for each event
        event_scores = []
        for event in future_events:
            # Calculate direct interest score
            interest_score = self._calculate_interest_score(
                user_interests, 
                event.get("category", [])
            )
            
            # Calculate social influence score
            social_score = self._calculate_social_influence_score(user_id, event.get("category", []))
            
            # Calculate collaborative filtering score
            collab_score = self._calculate_collaborative_filtering_score(user_id, event["id"])
            
            # Calculate recency score
            recency_score = 0.0
            start_time = event.get("start_time", 0)
            if start_time > 0:
                days_until_event = (start_time - now) / (24 * 3600)  # Convert seconds to days
                # Higher score for events that are coming soon (but not too soon)
                if 0 <= days_until_event <= 30:
                    recency_score = 1.0 - (days_until_event / 30)
            
            # Calculate distance score
            distance_score = 0.0
            venue = event.get("venue", {})
            if venue:
                distance_score = self._calculate_distance_score(user_location, venue)
            
            if is_new_user:
                # For new users, use enhanced interest scoring and add popularity
                enhanced_interest = self._calculate_enhanced_interest_score(user_interests, event)
                popularity_score = self._calculate_popularity_score(event)
                
                total_score = (
                    0.4 * enhanced_interest +  # Enhanced interest
                    0.2 * recency_score +      # Timing
                    0.2 * distance_score +     # Location
                    0.2 * popularity_score     # Popularity
                )
            else:
                # Combine scores with weights
                total_score = (
                    0.3 * interest_score + 
                    0.2 * social_score + 
                    0.15 * collab_score + 
                    0.15 * recency_score +
                    0.2 * distance_score  
                )
            
            event_scores.append({
                'event': event,
                'total_score': total_score,
                'explanation': {
                    'interest_score': interest_score,
                    'social_score': social_score,
                    'collaborative_score': collab_score,
                    'recency_score': recency_score,
                    'distance_score': distance_score
                }
            })
        
        # Sort events by score and get top N
        event_scores.sort(key=lambda x: x['total_score'], reverse=True)
        top_events = event_scores[:num_recommendations]
        
        return top_events

    def find_similar_users(self, user_id, max_users=5):
        """Find users with similar interests using cached data"""
        self.refresh_if_needed()
        
        if user_id not in self.users_data:
            return []
        
        target_user = self.users_data[user_id]
        target_interests = set(target_user.get('interests', []))
        
        if not target_interests:
            return []
        
        # Calculate similarity scores using cached data
        similarity_scores = []
        for other_id, user_data in self.users_data.items():
            if other_id == user_id:
                continue
                
            user_interests = set(user_data.get('interests', []))
            
            # Jaccard similarity between interest sets
            if not user_interests:
                continue
                
            intersection = len(target_interests.intersection(user_interests))
            union = len(target_interests.union(user_interests))
            similarity = intersection / union if union > 0 else 0
            
            similarity_scores.append({
                'user_id': other_id,
                'display_name': user_data.get('display_name', ''),
                'similarity': similarity,
                'interests': list(user_interests),
                'profile_image_url': user_data.get('profile_image_url')
            })
        
        # Sort by similarity and return top results
        similarity_scores.sort(key=lambda x: x['similarity'], reverse=True)
        return similarity_scores[:max_users]

    def recommend_connections(self, user_id, max_recommendations=5):
        """Recommend new connections based on shared interests and mutual connections"""
        self.refresh_if_needed()
        
        if user_id not in self.users_data:
            return []
        
        user_data = self.users_data[user_id]
        user_connections = set(user_data.get('connections', []))
        
        if user_id not in self.social_graph:
            return []
        
        # Find potential connections (friends of friends)
        potential_connections = set()
        for connection in user_connections:
            if connection in self.social_graph:
                for friend_of_friend in self.social_graph.neighbors(connection):
                    if friend_of_friend != user_id and friend_of_friend not in user_connections:
                        potential_connections.add(friend_of_friend)
        
        # Calculate scores for each potential connection using cached data
        connection_scores = []
        for potential_connection in potential_connections:
            if potential_connection not in self.users_data:
                continue
                
            connection_data = self.users_data[potential_connection]
            
            # Calculate interest similarity
            user_interests = set(user_data.get('interests', []))
            connection_interests = set(connection_data.get('interests', []))
            
            interest_similarity = 0
            if user_interests and connection_interests:
                common_interests = user_interests.intersection(connection_interests)
                interest_similarity = len(common_interests) / len(user_interests.union(connection_interests))
            
            # Calculate mutual connection strength
            mutual_connections = []
            for connection in user_connections:
                if connection in self.social_graph and potential_connection in self.social_graph.neighbors(connection):
                    mutual_connections.append(connection)
            
            mutual_connection_score = len(mutual_connections) / len(user_connections) if user_connections else 0
            
            # Combine scores
            total_score = 0.7 * interest_similarity + 0.3 * mutual_connection_score
            
            connection_scores.append({
                'user_id': potential_connection,
                'display_name': connection_data.get('display_name', ''),
                'total_score': total_score,
                'common_interests': list(user_interests.intersection(connection_interests)),
                'mutual_connections': mutual_connections,
                'profile_image_url': connection_data.get('profile_image_url')
            })
        
        # Sort by score and return top results
        connection_scores.sort(key=lambda x: x['total_score'], reverse=True)
        return connection_scores[:max_recommendations]