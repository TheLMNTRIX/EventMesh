import requests
import random
import json
import time
from datetime import datetime, timedelta
from math import cos, pi

API_BASE_URL = "http://localhost:8000/api"

# Reference location: Goa, India
BASE_LATITUDE = 15.421042
BASE_LONGITUDE = 73.980793
MAX_DISTANCE_KM = 15

# Provided interests
interests = [
    "tech", "music", "art", "food", "sports", "gaming", 
    "photography", "fashion", "literature", "science", 
    "movies", "travel", "fitness", "business", "education"
]

# Sample names for users
first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn", "Jamie", "Dakota", 
               "Skyler", "Reese", "Cameron", "Finley", "Blake", "Parker", "Hayden", "Drew", "Elliott", "Emerson"]
               
last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson"]

# Sample event titles and categories
event_titles = [
    "Tech Summit 2023", 
    "Music Festival Under the Stars",
    "Art Exhibition: Modern Perspectives",
    "Food & Wine Festival",
    "Sports Tournament Championship"
]

event_categories = [
    ["tech", "business", "education"],
    ["music", "art", "food"],
    ["art", "photography", "fashion"],
    ["food", "travel", "fitness"],
    ["sports", "fitness", "gaming"]
]

event_descriptions = [
    "Join us for a day of innovative tech talks, workshops, and networking.",
    "Experience amazing live performances from top artists in a beautiful outdoor setting.",
    "Explore contemporary art pieces from emerging and established artists.",
    "Taste exquisite cuisine and premium wines from around the world.",
    "Watch elite athletes compete for the championship title."
]

# Helper functions
def generate_random_interests(min_count=2, max_count=5):
    """Generate a random set of interests"""
    count = random.randint(min_count, max_count)
    return random.sample(interests, count)

def generate_email(name):
    """Generate an email from a name"""
    return f"{name.lower().replace(' ', '.')}@example.com"

def format_error(response):
    """Format error response for printing"""
    try:
        return f"Error: {response.status_code} - {response.json()}"
    except:
        return f"Error: {response.status_code} - {response.text}"

def print_response(response, action_msg):
    """Print API response with action message"""
    if response.status_code >= 200 and response.status_code < 300:
        print(f"✅ {action_msg} - Status: {response.status_code}")
        return response.json()
    else:
        print(f"❌ {action_msg} - Status: {response.status_code}")
        print(format_error(response))
        return None

def check_mutual_interests(user1_interests, user2_interests):
    """Check if two users have at least one mutual interest"""
    return bool(set(user1_interests) & set(user2_interests))

def validate_event_times(start_time, end_time, min_duration_hours=8):
    """Validate that event times are correct with minimum duration"""
    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
        return False
    
    if start_time >= end_time:
        return False
    
    # Check if duration is at least 8 hours
    duration = end_time - start_time
    return duration >= timedelta(hours=min_duration_hours)

def validate_schedule_item_times(item_start, item_end, event_start, event_end):
    """Validate that schedule item times are within event boundaries"""
    if not isinstance(item_start, datetime) or not isinstance(item_end, datetime):
        return False
    
    if item_start >= item_end:
        return False
    
    # Check if schedule item is contained within event times
    if item_start < event_start or item_end > event_end:
        return False
    
    return True

def generate_location_near_base(max_distance_km=MAX_DISTANCE_KM):
    """Generate a random location within specified distance of base coordinates"""
    # Convert max distance from km to degrees
    # Approximate conversion: 1 degree latitude = 111 km
    # Longitude conversion varies with latitude due to the Earth's curvature
    lat_offset_range = max_distance_km / 111.0
    
    # Adjust longitude range based on latitude (Earth narrows at higher latitudes)
    # cos(latitude in radians) gives the adjustment factor
    lon_offset_range = max_distance_km / (111.0 * cos(BASE_LATITUDE * pi / 180))
    
    # Generate random offsets within range
    lat_offset = random.uniform(-lat_offset_range, lat_offset_range)
    lon_offset = random.uniform(-lon_offset_range, lon_offset_range)
    
    # Add offsets to base coordinates
    lat = BASE_LATITUDE + lat_offset
    lng = BASE_LONGITUDE + lon_offset
    
    return lat, lng

# Main functions
def create_users(count=50):
    """Create users with overlapping interests"""
    print(f"\n{'=' * 50}\nGENERATING {count} USERS\n{'=' * 50}")
    
    users = []
    # Generate basic user data
    for i in range(count):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        name = f"{first_name} {last_name}"
        
        user = {
            # Let the API create the UID
            "display_name": name,
            "email": generate_email(name),
            "bio": f"Hi, I'm {first_name}. I enjoy {random.choice(interests)} and {random.choice(interests)}.",
            "profile_image_url": f"https://randomuser.me/api/portraits/{'men' if i % 2 == 0 else 'women'}/{i % 100}.jpg"
        }
        users.append(user)
    
    # Create users via API
    created_users = []
    for i, user in enumerate(users):
        print(f"Creating user {i+1}/{count}: {user['display_name']}")
        response = requests.post(f"{API_BASE_URL}/users", json=user)
        created_user = print_response(response, f"Created user {user['display_name']}")
        if created_user:
            # Initialize an interests array for each user
            created_user['interests'] = []
            created_users.append(created_user)
    
    # Assign interests to ensure overlapping
    print("\nAssigning interests to users...")
    for i, user in enumerate(created_users):
        # Every user gets 2-5 interests
        # Ensure there's some overlap with other users
        user_interests = generate_random_interests(2, 5)
        
        # Ensure some overlap with the next user (circular)
        next_user_index = (i + 1) % len(created_users)
        if i < len(created_users) - 1:
            # Add 1-2 shared interests with the next user
            shared_count = random.randint(1, 2)
            if len(user_interests) > shared_count:
                shared_interests = random.sample(user_interests, shared_count)
                # These will be used for the next user
                created_users[next_user_index]['temp_shared'] = shared_interests
        
        # Include shared interests from previous user
        if 'temp_shared' in user:
            for interest in user['temp_shared']:
                if interest not in user_interests:
                    user_interests.append(interest)
            del user['temp_shared']
        
        print(f"Setting interests for {user['display_name']}: {user_interests}")
        response = requests.post(
            f"{API_BASE_URL}/users/{user['uid']}/interests", 
            json={"interests": user_interests}
        )
        if print_response(response, f"Updated interests for {user['display_name']}"):
            # Store the interests in our local user object
            user['interests'] = user_interests
    
    print(f"Created {len(created_users)} users successfully")
    return created_users

def create_events(count=5, users=None):
    """Create events with schedules ensuring valid timing"""
    print(f"\n{'=' * 50}\nGENERATING {count} EVENTS\n{'=' * 50}")
    
    events = []
    now = datetime.now()
    
    for i in range(min(count, len(event_titles))):
        # Generate random start time in the next 30 days
        start_time = now + timedelta(days=random.randint(1, 30), hours=random.randint(0, 12))
        
        # Ensure event lasts at least 8 hours
        duration_hours = random.randint(8, 12)  # Between 8-12 hours
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Validate event times
        if not validate_event_times(start_time, end_time):
            print(f"⚠️ Invalid event times generated for {event_titles[i]}. Regenerating...")
            # This should not happen with our logic, but just in case
            continue
        
        print(f"Event duration: {duration_hours} hours")
        
        # Generate a venue within 15km of base location
        lat, lng = generate_location_near_base()
        
        # Create a schedule with 3-5 items distributed throughout the event
        schedule_items = []
        num_items = random.randint(3, 5)
        
        # Divide the event duration into roughly equal segments
        segment_duration = duration_hours / num_items
        
        for j in range(num_items):
            # Calculate segment boundaries
            segment_start = start_time + timedelta(hours=j * segment_duration)
            segment_end = start_time + timedelta(hours=(j + 1) * segment_duration)
            
            # Add some randomness within the segment
            buffer = min(60, segment_duration * 60 * 0.2)  # 20% of segment as buffer in minutes
            item_start = segment_start + timedelta(minutes=random.randint(0, int(buffer)))
            
            # Duration between 45-90 minutes, but ensure it ends before segment end
            max_duration = max(45, min(90, (segment_end - item_start).total_seconds() / 60 - 10))
            item_duration = random.randint(45, int(max_duration))
            item_end = item_start + timedelta(minutes=item_duration)
            
            # Validate schedule item times
            if not validate_schedule_item_times(item_start, item_end, start_time, end_time):
                print(f"⚠️ Invalid schedule item times. Adjusting...")
                # Ensure item is within event boundaries
                if item_start < start_time:
                    item_start = start_time + timedelta(minutes=random.randint(10, 30))
                if item_end > end_time:
                    item_end = end_time - timedelta(minutes=random.randint(10, 30))
                # Ensure item start is before end
                if item_start >= item_end:
                    item_end = item_start + timedelta(minutes=45)
                # Final check
                if not validate_schedule_item_times(item_start, item_end, start_time, end_time):
                    print(f"⚠️ Could not create valid schedule item. Skipping...")
                    continue
            
            print(f"  Schedule item {j+1}: {item_start.strftime('%H:%M')} - {item_end.strftime('%H:%M')}")
            
            schedule_items.append({
                "title": f"Session {j+1}: {random.choice(['Workshop', 'Talk', 'Panel', 'Networking'])}",
                "speaker_name": f"{random.choice(first_names)} {random.choice(last_names)}",
                "description": "Session description goes here.",
                "start_time": item_start.isoformat(),
                "end_time": item_end.isoformat()
            })
        
        # Create the event data
        event_data = {
            "title": event_titles[i],
            "description": event_descriptions[i],
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "venue": {
                "name": f"Venue {i+1}",
                "address": f"{random.randint(100, 999)} Main St, Goa, India",
                "latitude": lat,
                "longitude": lng
            },
            "category": event_categories[i],
            "image_url": f"https://picsum.photos/800/600?random={i}",
            "price": random.choice([0, 0, 10.99, 25.50, 49.99]),
            "organizer_name": f"{random.choice(first_names)} {random.choice(last_names)}",
            "organizer_email": "organizer@example.com",
            "organizer_phone": f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "schedule": schedule_items
        }
        
        print(f"Creating event {i+1}/{count}: {event_data['title']}")
        print(f"Event time: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"Event location: {lat:.6f}, {lng:.6f}")
        
        # Create event
        response = requests.post(f"{API_BASE_URL}/events", json=event_data)
        created_event = print_response(response, f"Created event {event_data['title']}")
        
        if created_event:
            print(f"Waiting 20 seconds to verify event creation...")
            time.sleep(20)
            
            # Verify event exists by fetching details
            print(f"Verifying event {created_event['id']} exists...")
            verify_response = requests.get(f"{API_BASE_URL}/events/{created_event['id']}")
            verified_event = print_response(verify_response, f"Verified event {event_data['title']}")
            
            if verified_event:
                events.append(verified_event)
                
                # Add RSVPs if we have users
                if users:
                    print(f"Adding RSVPs for event {verified_event['title']}...")
                    # Random sample of 5-15 users to attend this event
                    attending_users = random.sample(users, min(random.randint(5, 15), len(users)))
                    
                    for user in attending_users:
                        print(f"Adding RSVP for {user['display_name']} to {verified_event['title']}")
                        
                        # Try with a simple RSVP payload and explicit headers
                        rsvp_data = {
                            "status": "attending"
                        }
                        
                        try:
                            # Log detailed request information
                            rsvp_url = f"{API_BASE_URL}/events/{verified_event['id']}/rsvp?user_id={user['uid']}"
                            print(f"Making RSVP request to: {rsvp_url}")
                            print(f"With data: {rsvp_data}")
                            
                            # Add a delay between requests to avoid overwhelming the server
                            time.sleep(1)
                            
                            # Make request with explicit content-type header
                            headers = {"Content-Type": "application/json"}
                            rsvp_response = requests.post(rsvp_url, json=rsvp_data, headers=headers)
                            
                            # Detailed logging for any error
                            if rsvp_response.status_code >= 400:
                                print(f"RSVP Error details:")
                                print(f"Status code: {rsvp_response.status_code}")
                                print(f"Response headers: {dict(rsvp_response.headers)}")
                                try:
                                    print(f"Response content: {rsvp_response.text}")
                                except:
                                    print("Could not print response content")
                            
                            print_response(rsvp_response, f"Added RSVP for {user['display_name']}")
                            
                        except Exception as e:
                            print(f"❌ Exception while making RSVP request: {str(e)}")
            else:
                print(f"⚠️ Event {created_event['id']} could not be verified! Skipping RSVPs.")
    
    print(f"Created {len(events)} events successfully")
    return events

def create_connections(users):
    """Create connections between users with mutual interests"""
    print(f"\n{'=' * 50}\nGENERATING CONNECTIONS\n{'=' * 50}")
    
    connection_count = 0
    
    # Each user will send 3-5 connection requests (or as many as possible with mutual interests)
    for user in users:
        # Find all users with at least one mutual interest
        potential_connections = []
        for other_user in users:
            if other_user['uid'] != user['uid'] and check_mutual_interests(user['interests'], other_user['interests']):
                potential_connections.append(other_user)
        
        if not potential_connections:
            print(f"⚠️ No users with mutual interests found for {user['display_name']}")
            continue
        
        # Select 3-5 random users to connect with (or fewer if not enough with mutual interests)
        request_count = min(random.randint(3, 5), len(potential_connections))
        to_connect = random.sample(potential_connections, request_count)
        
        for other_user in to_connect:
            mutual = set(user['interests']) & set(other_user['interests'])
            print(f"Creating connection request: {user['display_name']} -> {other_user['display_name']}")
            print(f"  Mutual interests: {', '.join(mutual)}")
            
            connection_data = {
                "from_user_id": user['uid'],
                "to_user_id": other_user['uid']
            }
            
            response = requests.post(f"{API_BASE_URL}/connections/request", json=connection_data)
            connection_result = print_response(
                response, 
                f"Created connection request from {user['display_name']} to {other_user['display_name']}"
            )
            
            if connection_result:
                # 70% chance to accept the connection after a delay
                if random.random() < 0.7:
                    # Wait 5-10 seconds before accepting
                    delay = random.uniform(5, 10)
                    print(f"Waiting {delay:.1f} seconds before accepting connection...")
                    time.sleep(delay)
                    
                    # Accept the connection - FIXED to match the API expectation
                    print(f"{other_user['display_name']} is accepting connection from {user['display_name']}")
                    
                    # The API expects a ConnectionResponse model with:
                    # - request_id: the ID of the user who SENT the request
                    # - user_id: the ID of the user RESPONDING to the request
                    # - status: "accept" or "decline"
                    accept_data = {
                        "request_id": user['uid'],     # ID of the user who sent the request
                        "user_id": other_user['uid'],  # ID of the user accepting the request
                        "status": "accept"
                    }
                    
                    # Use the "find" endpoint which looks up by user IDs instead of connection ID
                    accept_response = requests.post(
                        f"{API_BASE_URL}/connections/respond/find", 
                        json=accept_data
                    )
                    print_response(
                        accept_response, 
                        f"{other_user['display_name']} accepted connection from {user['display_name']}"
                    )
                connection_count += 1
    
    print(f"Created {connection_count} connections")

def create_feedback(users, events):
    """Create feedback for events"""
    print(f"\n{'=' * 50}\nGENERATING EVENT FEEDBACK\n{'=' * 50}")
    
    feedback_count = 0
    
    for event in events:
        # Get 2-5 random users to provide feedback
        feedback_users = random.sample(users, min(random.randint(2, 5), len(users)))
        
        for user in feedback_users:
            print(f"Creating feedback from {user['display_name']} for {event['title']}")
            
            feedback_data = {
                "rating": random.randint(3, 5),  # Mostly positive ratings
                "comment": random.choice([
                    "Really enjoyed this event!",
                    "Great organization and content.",
                    "Would definitely attend again.",
                    "Excellent speakers and venue.",
                    "Learned a lot from this event."
                ])
            }
            
            response = requests.post(
                f"{API_BASE_URL}/feedback/{event['id']}?user_id={user['uid']}", 
                json=feedback_data
            )
            
            if print_response(response, f"Created feedback from {user['display_name']} for {event['title']}"):
                feedback_count += 1
    
    print(f"Created {feedback_count} feedback entries")

def update_user_locations(users):
    """Update random locations for users"""
    print(f"\n{'=' * 50}\nUPDATING USER LOCATIONS\n{'=' * 50}")
    
    for user in users:
        # Generate a random location within 15km of base location in Goa
        lat, lng = generate_location_near_base()
        
        location_data = {
            "latitude": lat,
            "longitude": lng
        }
        
        print(f"Updating location for {user['display_name']}: {lat:.6f}, {lng:.6f}")
        response = requests.post(
            f"{API_BASE_URL}/users/{user['uid']}/location", 
            json=location_data
        )
        print_response(response, f"Updated location for {user['display_name']}")

def main():
    print(f"\n{'=' * 50}\nEVENTMESH DATA GENERATION SCRIPT\n{'=' * 50}")
    print("This script will generate sample data for the EventMesh application")
    print(f"All locations will be within 15km of: {BASE_LATITUDE}, {BASE_LONGITUDE} (Goa, India)")
    
    # Create users
    users = create_users(50)
    
    if not users:
        print("Failed to create users. Exiting.")
        return
    
    # Update user locations
    update_user_locations(users)
    
    # Create events
    events = create_events(5, users)
    
    # Create connections between users with mutual interests
    create_connections(users)
    
    # Create feedback
    if events:
        create_feedback(users, events)
    
    print(f"\n{'=' * 50}\nDATA GENERATION COMPLETE\n{'=' * 50}")
    print(f"Generated {len(users)} users")
    print(f"Generated {len(events)} events")
    print("Run the admin migration endpoints to ensure data consistency:")
    print(f"POST {API_BASE_URL}/admin/recalculate-counts")
    print(f"POST {API_BASE_URL}/admin/update-connections-arrays")

if __name__ == "__main__":
    main()