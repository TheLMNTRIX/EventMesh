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

# New sample names for users
first_names = [
    "Rohan", "Priya", "Vikram", "Neha", "Arjun", "Meera", "Raj", "Ananya", "Karan", "Divya",
    "Aryan", "Aisha", "Nikhil", "Tanya", "Aditya", "Zara", "Kabir", "Nisha", "Rahul", "Maya",
    "Varun", "Pooja", "Sahil", "Kavya", "Rishi", "Isha", "Aarush", "Sanya", "Dev", "Kiara",
    "Rohit", "Anjali", "Vihaan", "Kritika", "Shaurya", "Deepika", "Yash", "Anushka", "Armaan", "Riya",
    "Mihir", "Anika", "Vivaan", "Tanvi", "Aarav", "Ishita", "Dhruv", "Sana", "Rishaan", "Shreya"
]

last_names = [
    "Sharma", "Patel", "Singh", "Verma", "Gupta", "Kapoor", "Kumar", "Joshi", "Shah", "Reddy",
    "Bose", "Malhotra", "Banerjee", "Khanna", "Agarwal", "Iyer", "Chatterjee", "Mathur", "Nair", "Menon",
    "Rao", "Desai", "Mehta", "Chauhan", "Chopra", "Jain", "Das", "Kaur", "Mukherjee", "Gandhi",
    "Shetty", "Bhatia", "Roy", "Garg", "Sinha", "Trivedi", "Malik", "Saxena", "Suri", "Ahuja",
    "Sachdeva", "Lal", "Bhatt", "Rajput", "Thakur", "Arora", "Pradhan", "Tiwari", "Srivastava", "Chaudhry"
]

# New sample event titles
event_titles = [
    "Innovation Conference 2023",
    "Monsoon Music Festival",
    "Cultural Heritage Exhibition",
    "Beachside Yoga Retreat",
    "Coastal Culinary Festival",
    "Digital Marketing Workshop",
    "Startup Pitch Competition",
    "Literary Festival Goa",
    "Sustainable Living Expo",
    "Wellness & Mindfulness Retreat",
    "Entrepreneurship Summit",
    "Artificial Intelligence Conference",
    "Photography Exhibition: Coastal Life",
    "Dance & Music Celebration",
    "Adventure Sports Weekend"
]

# New event categories
event_categories = [
    ["tech", "business", "education"],
    ["music", "art", "entertainment"],
    ["art", "culture", "history"],
    ["fitness", "wellness", "health"],
    ["food", "travel", "culture"],
    ["tech", "business", "social"],
    ["business", "tech", "education"],
    ["literature", "art", "education"],
    ["science", "environment", "education"],
    ["fitness", "health", "wellness"],
    ["business", "tech", "education"],
    ["tech", "science", "education"],
    ["photography", "art", "culture"],
    ["music", "art", "entertainment"],
    ["sports", "fitness", "travel"]
]

# New event descriptions
event_descriptions = [
    "Join thought leaders and innovators for a day of cutting-edge insights and networking.",
    "Experience the magic of monsoon with live music performances on Goa's beautiful beaches.",
    "Discover the rich cultural heritage of Goa through artifacts, stories, and interactive exhibits.",
    "Rejuvenate mind and body with beach yoga sessions guided by experienced instructors.",
    "Indulge in local and international cuisines with special emphasis on coastal delicacies.",
    "Master the latest digital marketing strategies from industry experts and practitioners.",
    "Watch promising startups pitch their revolutionary ideas to investors and mentors.",
    "Celebrate literature with book launches, author interactions, and engaging discussions.",
    "Learn practical approaches to sustainable living through workshops and demonstrations.",
    "Find your center with guided meditation, mindfulness practices, and holistic health activities.",
    "Connect with successful entrepreneurs, investors, and mentors to accelerate your business journey.",
    "Explore the frontiers of AI with keynotes from leading researchers and practical applications.",
    "View stunning photographs capturing the essence of coastal living and natural beauty.",
    "Immerse yourself in diverse dance forms and musical traditions from across India.",
    "Challenge yourself with thrilling adventure activities including paragliding, trekking, and water sports."
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
    """Check if two users have at least two mutual interests"""
    mutual = set(user1_interests) & set(user2_interests)
    return len(mutual) >= 2

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
def create_users(count=150):
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
        # Every user gets 3-6 interests (increased to ensure more overlaps)
        user_interests = generate_random_interests(3, 6)
        
        # Ensure some overlap with the next user (circular)
        next_user_index = (i + 1) % len(created_users)
        if i < len(created_users) - 1:
            # Add 2-3 shared interests with the next user
            shared_count = random.randint(2, 3)
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

def create_events(count=15, users=None):
    """Create events with schedules ensuring valid timing"""
    print(f"\n{'=' * 50}\nGENERATING {count} EVENTS\n{'=' * 50}")
    
    events = []
    now = datetime.now()
    
    # First 7 events will be in the past and have organizer@example.com
    for i in range(min(7, count)):
        # Generate random start time in the past 30 days
        days_ago = random.randint(1, 30)
        start_time = now - timedelta(days=days_ago, hours=random.randint(0, 12))
        
        # Ensure event lasts at least 8 hours
        duration_hours = random.randint(8, 12)  # Between 8-12 hours
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Validate event times
        if not validate_event_times(start_time, end_time):
            print(f"⚠️ Invalid event times generated for {event_titles[i]}. Regenerating...")
            # Adjust end_time to ensure it's valid
            end_time = start_time + timedelta(hours=8)
        
        print(f"Past event duration: {duration_hours} hours, {days_ago} days ago")
        
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
            "organizer_email": "organizer@example.com",  # First 7 events have this email
            "organizer_phone": f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "schedule": schedule_items
        }
        
        print(f"Creating past event {i+1}/7: {event_data['title']}")
        print(f"Event time: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"Event location: {lat:.6f}, {lng:.6f}")
        
        # Create event
        response = requests.post(f"{API_BASE_URL}/events", json=event_data)
        created_event = print_response(response, f"Created event {event_data['title']}")
        
        if created_event:
            print(f"Waiting 10 seconds to verify event creation...")
            time.sleep(10)
            
            # Verify event exists by fetching details
            print(f"Verifying event {created_event['id']} exists...")
            verify_response = requests.get(f"{API_BASE_URL}/events/{created_event['id']}")
            verified_event = print_response(verify_response, f"Verified event {event_data['title']}")
            
            if verified_event:
                events.append(verified_event)
    
    # Remaining events will be in the future with different organizer emails
    for i in range(7, count):
        # Generate random start time in the next 30 days
        start_time = now + timedelta(days=random.randint(1, 30), hours=random.randint(0, 12))
        
        # Ensure event lasts at least 8 hours
        duration_hours = random.randint(8, 12)  # Between 8-12 hours
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Validate event times
        if not validate_event_times(start_time, end_time):
            print(f"⚠️ Invalid event times generated for {event_titles[i]}. Regenerating...")
            # Adjust end_time to ensure it's valid
            end_time = start_time + timedelta(hours=8)
        
        print(f"Future event duration: {duration_hours} hours")
        
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
        
        # Generate a different organizer email for remaining events
        organizer_first_name = random.choice(first_names).lower()
        organizer_email = f"{organizer_first_name}.organizer@eventmesh.com"
        
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
            "organizer_email": organizer_email,  # Different organizer email for remaining events
            "organizer_phone": f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "schedule": schedule_items
        }
        
        print(f"Creating future event {i-6}/{count-7}: {event_data['title']}")
        print(f"Event time: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"Event location: {lat:.6f}, {lng:.6f}")
        
        # Create event
        response = requests.post(f"{API_BASE_URL}/events", json=event_data)
        created_event = print_response(response, f"Created event {event_data['title']}")
        
        if created_event:
            print(f"Waiting 10 seconds to verify event creation...")
            time.sleep(10)
            
            # Verify event exists by fetching details
            print(f"Verifying event {created_event['id']} exists...")
            verify_response = requests.get(f"{API_BASE_URL}/events/{created_event['id']}")
            verified_event = print_response(verify_response, f"Verified event {event_data['title']}")
            
            if verified_event:
                events.append(verified_event)
    
    # Add 40-80 attendees for each event
    if users and events:
        for event in events:
            attendee_count = random.randint(40, 80)
            attendee_count = min(attendee_count, len(users))
            print(f"Adding {attendee_count} attendees to event {event['title']}...")
            
            # Select random users to attend this event
            attending_users = random.sample(users, attendee_count)
            
            for user in attending_users:
                print(f"Adding RSVP for {user['display_name']} to {event['title']}")
                
                # Simple RSVP payload
                rsvp_data = {
                    "status": "attending"
                }
                
                try:
                    # Make RSVP request
                    rsvp_url = f"{API_BASE_URL}/events/{event['id']}/rsvp?user_id={user['uid']}"
                    rsvp_response = requests.post(rsvp_url, json=rsvp_data)
                    print_response(rsvp_response, f"Added RSVP for {user['display_name']}")
                except Exception as e:
                    print(f"❌ Exception while making RSVP request: {str(e)}")
    
    print(f"Created {len(events)} events successfully")
    return events

def create_connections(users):
    """Create connections between users with mutual interests"""
    print(f"\n{'=' * 50}\nGENERATING CONNECTIONS\n{'=' * 50}")
    
    connection_count = 0
    
    # Each user will send 5-10 connection requests (or as many as possible with mutual interests)
    for user in users:
        # Find all users with at least two mutual interests
        potential_connections = []
        for other_user in users:
            if other_user['uid'] != user['uid'] and check_mutual_interests(user['interests'], other_user['interests']):
                potential_connections.append(other_user)
        
        if not potential_connections:
            print(f"⚠️ No users with 2+ mutual interests found for {user['display_name']}")
            continue
        
        # Select 5-10 random users to connect with (or fewer if not enough with mutual interests)
        request_count = min(random.randint(5, 10), len(potential_connections))
        to_connect = random.sample(potential_connections, request_count)
        
        for other_user in to_connect:
            mutual = set(user['interests']) & set(other_user['interests'])
            print(f"Creating connection request: {user['display_name']} -> {other_user['display_name']}")
            print(f"  Mutual interests ({len(mutual)}): {', '.join(mutual)}")
            
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
                # 80% chance to accept the connection
                if random.random() < 0.8:
                    # Accept the connection
                    print(f"{other_user['display_name']} is accepting connection from {user['display_name']}")
                    
                    accept_data = {
                        "request_id": user['uid'],
                        "user_id": other_user['uid'],
                        "status": "accept"
                    }
                    
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
        # Get 15-25 random users to provide feedback
        feedback_users = random.sample(users, min(random.randint(15, 25), len(users)))
        
        for user in feedback_users:
            print(f"Creating feedback from {user['display_name']} for {event['title']}")
            
            # 70% positive, 30% negative feedback
            if random.random() < 0.7:
                # Positive feedback (3-5 stars)
                rating = random.randint(3, 5)
                comment = random.choice([
                    "Really enjoyed this event!",
                    "Great organization and content.",
                    "Would definitely attend again.",
                    "Excellent speakers and venue.",
                    "Learned a lot from this event."
                ])
            else:
                # Negative feedback (1-2 stars)
                rating = random.randint(1, 2)
                comment = random.choice([
                    "Poor organization, would not recommend.",
                    "The content was disappointing.",
                    "Too crowded and poorly managed.",
                    "Speakers were not prepared well.",
                    "Not worth the price of admission.",
                    "Schedule was not followed properly."
                ])
            
            feedback_data = {
                "rating": rating,
                "comment": comment
            }
            
            response = requests.post(
                f"{API_BASE_URL}/feedback/{event['id']}?user_id={user['uid']}", 
                json=feedback_data
            )
            
            if print_response(response, f"Created feedback from {user['display_name']} for {event['title']}"):
                feedback_count += 1
    
    print(f"Created {feedback_count} feedback entries")

def main():
    print(f"\n{'=' * 50}\nEVENTMESH MOCK DATA GENERATION SCRIPT\n{'=' * 50}")
    print("This script will generate additional sample data for the EventMesh application")
    print(f"All locations will be within 15km of: {BASE_LATITUDE}, {BASE_LONGITUDE} (Goa, India)")
    
    # Create users
    users = create_users(150)
    
    if not users:
        print("Failed to create users. Exiting.")
        return
    
    # Create events (7 past events + 8 future events)
    events = create_events(15, users)
    
    # Create connections between users with mutual interests
    create_connections(users)
    
    # Create feedback
    if events:
        create_feedback(users, events)
    
    print(f"\n{'=' * 50}\nMOCK DATA GENERATION COMPLETE\n{'=' * 50}")
    print(f"Generated {len(users)} users")
    print(f"Generated {len(events)} events")
    print("Run the admin migration endpoints to ensure data consistency:")
    print(f"POST {API_BASE_URL}/admin/recalculate-counts")
    print(f"POST {API_BASE_URL}/admin/update-connections-arrays")

if __name__ == "__main__":
    main()