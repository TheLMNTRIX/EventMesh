from firebase_admin import db, storage, firestore
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

# Import the config module to initialize Firebase
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import db as firebase_db  # This will execute the initialization code

class FirebaseService:
    def __init__(self):
        self.db = firestore.client()
        
    # User methods
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user in Firestore"""
        user_ref = self.db.collection('users').document(user_data['uid'])
        user_data['created_at'] = firestore.SERVER_TIMESTAMP
        user_ref.set(user_data)
        created_user = user_ref.get().to_dict()
        return created_user
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID"""
        user_ref = self.db.collection('users').document(user_id)
        user = user_ref.get()
        if user.exists:
            return user.to_dict()
        return None
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data"""
        user_ref = self.db.collection('users').document(user_id)
        user_data['updated_at'] = firestore.SERVER_TIMESTAMP
        user_ref.update(user_data)
        updated_user = user_ref.get().to_dict()
        return updated_user
    
    # Event methods
    async def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new event"""
        event_ref = self.db.collection('events').document()
        event_data['id'] = event_ref.id
        event_data['created_at'] = firestore.SERVER_TIMESTAMP
        event_ref.set(event_data)
        created_event = event_ref.get().to_dict()
        return created_event
    
    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get an event by ID"""
        event_ref = self.db.collection('events').document(event_id)
        event = event_ref.get()
        if event.exists:
            return event.to_dict()
        return None
    
    async def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update event data"""
        event_ref = self.db.collection('events').document(event_id)
        event_data['updated_at'] = firestore.SERVER_TIMESTAMP
        event_ref.update(event_data)
        updated_event = event_ref.get().to_dict()
        return updated_event
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        event_ref = self.db.collection('events').document(event_id)
        event_ref.delete()
        return True
    
    async def get_events(self, filters: Dict[str, Any] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get events with optional filters"""
        events_ref = self.db.collection('events')
        query = events_ref.limit(limit)
        
        if filters:
            if 'categories' in filters and filters['categories']:
                query = query.where('category', 'array_contains_any', filters['categories'])
            
            if 'start_date' in filters and filters['start_date']:
                query = query.where('start_time', '>=', filters['start_date'])
                
            if 'end_date' in filters and filters['end_date']:
                query = query.where('start_time', '<=', filters['end_date'])
                
            if 'free_only' in filters and filters['free_only']:
                query = query.where('price', '==', 0)
        
        events = []
        for doc in query.stream():
            events.append(doc.to_dict())
            
        return events
    
    # Connection methods
    async def create_connection_request(self, from_user_id: str, to_user_id: str) -> Dict[str, Any]:
        """Create a connection request between users"""
        connection_ref = self.db.collection('connections').document()
        connection_data = {
            'id': connection_ref.id,
            'from_user_id': from_user_id,
            'to_user_id': to_user_id,
            'status': 'pending',
            'created_at': firestore.SERVER_TIMESTAMP
        }
        connection_ref.set(connection_data)
        return connection_data
    
    async def update_connection_status(self, connection_id: str, status: str) -> Dict[str, Any]:
        """Update connection request status"""
        connection_ref = self.db.collection('connections').document(connection_id)
        connection_ref.update({
            'status': status,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        return connection_ref.get().to_dict()
    
    async def get_user_connections(self, user_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get user's connections with optional status filter"""
        connections = []
        
        # Get connections where user is the requester
        from_query = self.db.collection('connections').where('from_user_id', '==', user_id)
        if status:
            from_query = from_query.where('status', '==', status)
            
        for doc in from_query.stream():
            connections.append(doc.to_dict())
            
        # Get connections where user is the receiver
        to_query = self.db.collection('connections').where('to_user_id', '==', user_id)
        if status:
            to_query = to_query.where('status', '==', status)
            
        for doc in to_query.stream():
            connections.append(doc.to_dict())
            
        return connections
    
    async def get_connection(self, connection_id: str) -> Dict[str, Any]:
        """Get a single connection by ID"""
        connection_ref = self.db.collection('connections').document(connection_id)
        connection = connection_ref.get()
        if connection.exists:
            return connection.to_dict()
        return None
    
    # RSVP methods
    async def update_event_rsvp(self, event_id: str, user_id: str, status: str) -> Dict[str, Any]:
        """Update user's RSVP status for an event"""
        # We only accept "attending" status now
        if status != "attending":
            return None
        
        event_ref = self.db.collection('events').document(event_id)
        event_data = event_ref.get().to_dict()
        
        if not event_data:
            return None
        
        # Initialize attendees array if it doesn't exist
        attendees = event_data.get('attendees', [])
        
        # Check if user is already in attendees
        already_attending = any(att.get('user_id') == user_id for att in attendees)
        
        if not already_attending:
            # Add the user to attendees array
            # Use a current datetime instead of SERVER_TIMESTAMP for the nested structure
            attendee_data = {
                'user_id': user_id,
                'rsvp_date': datetime.now().isoformat()  # Use ISO format string instead of SERVER_TIMESTAMP
            }
            attendees.append(attendee_data)
            
            # Update the event document with new attendee and count
            attendees_count = len(attendees)
            
            event_ref.update({
                'attendees': attendees,
                'attendees_count': attendees_count,
                'updated_at': firestore.SERVER_TIMESTAMP  # SERVER_TIMESTAMP can be used at the top level
            })
            
            # Increment the user's events_attended counter
            user_ref = self.db.collection('users').document(user_id)
            user_ref.update({
                'events_attended': firestore.Increment(1),
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
            print(f"Added user {user_id} to event {event_id}. New attendee count: {attendees_count}")
            print(f"Incremented events_attended counter for user {user_id}")
        
        return event_ref.get().to_dict()

    async def get_event_attendees(self, event_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get attendees for an event"""
        # Since we're now using an array and only supporting "attending" status,
        # the status parameter is ignored
        
        event_ref = self.db.collection('events').document(event_id)
        event = event_ref.get().to_dict()
        
        if not event:
            return []
        
        # Return the attendees array
        return event.get('attendees', [])
    
    # Feedback methods
    async def create_event_feedback(self, event_id: str, user_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create feedback for an event"""
        event_ref = self.db.collection('events').document(event_id)
        feedback_ref = event_ref.collection('feedback').document(user_id)
        
        feedback_data['user_id'] = user_id
        feedback_data['created_at'] = firestore.SERVER_TIMESTAMP
        
        feedback_ref.set(feedback_data)
        return feedback_ref.get().to_dict()
    
    async def get_event_feedback(self, event_id: str) -> List[Dict[str, Any]]:
        """Get all feedback for an event"""
        event_ref = self.db.collection('events').document(event_id)
        feedback_ref = event_ref.collection('feedback')
        
        feedback = []
        for doc in feedback_ref.stream():
            feedback.append(doc.to_dict())
            
        return feedback

    async def delete_event_feedback(self, event_id: str, user_id: str) -> bool:
        """Delete feedback for an event from a user"""
        event_ref = self.db.collection('events').document(event_id)
        feedback_ref = event_ref.collection('feedback').document(user_id)
        
        feedback = feedback_ref.get()
        if not feedback.exists:
            return False
        
        feedback_ref.delete()
        return True

    async def recalculate_counts(self):
        """Recalculate all event attendee counts and user connection counts"""
        # Recalculate event attendee counts
        events_ref = self.db.collection('events')
        for event_doc in events_ref.stream():
            event_id = event_doc.id
            attendees_ref = event_doc.reference.collection('attendees')
            attending_query = attendees_ref.where('status', '==', 'attending')
            attending_count = len(list(attending_query.stream()))
            
            # Update the event document
            event_doc.reference.update({'attendees_count': attending_count})
            print(f"Updated event {event_id} with {attending_count} attendees")
        
        # Recalculate user connection counts
        users_ref = self.db.collection('users')
        connections_ref = self.db.collection('connections')
        
        for user_doc in users_ref.stream():
            user_id = user_doc.id
            # Count accepted connections where user is either from_user_id or to_user_id
            from_count = len(list(connections_ref.where('from_user_id', '==', user_id).where('status', '==', 'accepted').stream()))
            to_count = len(list(connections_ref.where('to_user_id', '==', user_id).where('status', '==', 'accepted').stream()))
            
            # Update user document
            user_doc.reference.update({'connection_count': from_count + to_count})
            print(f"Updated user {user_id} with {from_count + to_count} connections")

    async def update_connections_arrays(self):
        """Update the connections array for all users based on accepted connections"""
        # Get all accepted connections
        connections_ref = self.db.collection('connections')
        accepted_connections = connections_ref.where('status', '==', 'accepted').stream()
        
        # Keep track of which users we've updated
        updated_users = set()
        
        for conn in accepted_connections:
            conn_data = conn.to_dict()
            from_user_id = conn_data.get('from_user_id')
            to_user_id = conn_data.get('to_user_id')
            
            if from_user_id and to_user_id:
                # Update from_user
                from_user = await self.get_user(from_user_id)
                if from_user:
                    connections = from_user.get('connections', [])
                    if to_user_id not in connections:
                        connections.append(to_user_id)
                        await self.update_user(from_user_id, {'connections': connections})
                        updated_users.add(from_user_id)
                
                # Update to_user
                to_user = await self.get_user(to_user_id)
                if to_user:
                    connections = to_user.get('connections', [])
                    if from_user_id not in connections:
                        connections.append(from_user_id)
                        await self.update_user(to_user_id, {'connections': connections})
                        updated_users.add(to_user_id)
                        
                print(f"Updated connection arrays for users {from_user_id} and {to_user_id}")
        
        # Return count of updated users
        return len(updated_users)

    async def migrate_data_structures(self):
        """
        Migrate existing data to conform to new data structures:
        1. Convert event attendee subcollections to arrays
        2. Update user connection arrays
        3. Ensure consistent counts in both events and user documents
        """
        result = {
            "events_updated": 0,
            "users_updated": 0,
            "connections_processed": 0
        }
        
        # 1. Migrate event attendees from subcollections to arrays
        events_ref = self.db.collection('events')
        events = events_ref.stream()
        
        for event_doc in events:
            event_id = event_doc.id
            event_data = event_doc.to_dict()
            
            # Check if this event already has an attendees array
            if 'attendees' in event_data:
                print(f"Event {event_id} already has attendees array")
                continue
                
            # Look for attendees subcollection
            attendees_ref = event_doc.reference.collection('attendees')
            attendees_docs = attendees_ref.where('status', '==', 'attending').stream()
            
            # Convert to array format
            attendees_array = []
            for att_doc in attendees_docs:
                att_data = att_doc.to_dict()
                attendee_entry = {
                    'user_id': att_data.get('user_id'),
                    'rsvp_date': att_data.get('rsvp_date', firestore.SERVER_TIMESTAMP)
                }
                attendees_array.append(attendee_entry)
            
            # Update event with new structure
            if attendees_array:
                event_doc.reference.update({
                    'attendees': attendees_array,
                    'attendees_count': len(attendees_array)
                })
                print(f"Updated event {event_id} with {len(attendees_array)} attendees")
                result["events_updated"] += 1
        
        # 2. Process connections and update user connection arrays
        connections_ref = self.db.collection('connections')
        accepted_connections = connections_ref.where('status', '==', 'accepted').stream()
        
        connection_map = {}  # user_id -> [connected_user_ids]
        
        # Build the connections map
        for conn in accepted_connections:
            conn_data = conn.to_dict()
            from_user_id = conn_data.get('from_user_id')
            to_user_id = conn_data.get('to_user_id')
            
            if from_user_id and to_user_id:
                # Add to from_user's connections
                if from_user_id not in connection_map:
                    connection_map[from_user_id] = []
                if to_user_id not in connection_map[from_user_id]:
                    connection_map[from_user_id].append(to_user_id)
                    
                # Add to to_user's connections
                if to_user_id not in connection_map:
                    connection_map[to_user_id] = []
                if from_user_id not in connection_map[to_user_id]:
                    connection_map[to_user_id].append(from_user_id)
                    
                result["connections_processed"] += 1
        
        # Update all users with their connections
        users_ref = self.db.collection('users')
        for user_id, connections in connection_map.items():
            user_ref = users_ref.document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                
                # Update connection array
                existing_connections = user_data.get('connections', [])
                for conn_id in connections:
                    if conn_id not in existing_connections:
                        existing_connections.append(conn_id)
                
                # Update connection count
                conn_count = len(existing_connections)
                
                # Update the user document
                user_ref.update({
                    'connections': existing_connections,
                    'connection_count': conn_count
                })
                
                print(f"Updated user {user_id} with {conn_count} connections")
                result["users_updated"] += 1
        
        return result

    async def recalculate_events_attended(self):
        """Recalculate all users' events_attended based on event RSVPs"""
        # Get all users
        users_ref = self.db.collection('users')
        users = list(users_ref.stream())
        
        # Get all events
        events_ref = self.db.collection('events')
        events = list(events_ref.stream())
        
        # For each user, count the number of events they're attending
        updated_count = 0
        for user_doc in users:
            user_id = user_doc.id
            user_data = user_doc.to_dict()
            
            # Count events the user is attending
            events_attended = 0
            for event_doc in events:
                event_data = event_doc.to_dict()
                attendees = event_data.get('attendees', [])
                
                # Check if user is in attendees
                if any(att.get('user_id') == user_id for att in attendees):
                    events_attended += 1
            
            # Update the user document if the count has changed
            if user_data.get('events_attended', 0) != events_attended:
                user_doc.reference.update({
                    'events_attended': events_attended,
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
                print(f"Updated events_attended for user {user_id}: {events_attended}")
                updated_count += 1
        
        return updated_count

firebase_service = FirebaseService()# Initialize service
__all__ = ["firebase_service"]