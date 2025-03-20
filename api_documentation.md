# EventMesh API Documentation

## Base URL

All API requests should be made to:

```
https://api.eventmesh.com/api
```

*For development, use:* `http://localhost:8000/api`

## Authentication

Authentication details will be provided separately. All authenticated endpoints require the appropriate tokens in the request headers.

## Endpoints

### Users

#### Create User

Create a new user profile.

**Endpoint:** `POST /users`

**Request Body:**
```json
{
  "uid": "string", 
  "display_name": "string",
  "email": "string",
  "bio": "string", 
  "profile_image_url": "string" 
}
```

> Note: Fields marked with an asterisk (*) are optional.

**Response:** User object
```json
{
  "id": "string",
  "uid": "string",
  "display_name": "string",
  "email": "string",
  "bio": "string",
  "profile_image_url": "string",
  "interests": ["string"],
  "location": {
    "latitude": number,
    "longitude": number
  },
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Get User

Get user profile by ID.

**Endpoint:** `GET /users/{user_id}`

**Path Parameters:**
- `user_id` (string, required): User ID

**Response:** User object

#### Get User by Email

Find a user by email address.

**Endpoint:** `GET /users/by-email/{email}`

**Path Parameters:**
- `email` (string, required): Email address

**Response:** User object

#### Update User

Update a user's profile information.

**Endpoint:** `PUT /users/{user_id}`

**Path Parameters:**
- `user_id` (string, required): User ID

**Request Body:**
```json
{
  "display_name": "string",
  "bio": "string",
  "profile_image_url": "string"
}
```

**Response:** Updated User object

#### Update User Interests

Update a user's interests.

**Endpoint:** `POST /users/{user_id}/interests`

**Path Parameters:**
- `user_id` (string, required): User ID

**Request Body:**
```json
{
  "interests": ["string"]
}
```

**Response:** Updated User object

#### Update User Location

Update a user's current location.

**Endpoint:** `POST /users/{user_id}/location`

**Path Parameters:**
- `user_id` (string, required): User ID

**Request Body:**
```json
{
  "latitude": number,
  "longitude": number
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Location updated"
}
```

#### Get User Events

Get events that a user is attending or interested in.

**Endpoint:** `GET /users/{user_id}/events`

**Path Parameters:**
- `user_id` (string, required): User ID

**Query Parameters:**
- `status` (string, optional): Filter by RSVP status (e.g., "attending")

**Response:** Array of Event objects

---

### Events

#### Create Event

Create a new event.

**Endpoint:** `POST /events`

**Request Body:**
```json
{
  "title": "string",
  "description": "string",
  "start_time": "datetime",
  "end_time": "datetime",
  "venue": {
    "name": "string",
    "address": "string",
    "latitude": number,
    "longitude": number
  },
  "category": ["string"],
  "image_url": "string",
  "price": number,
  "organizer_name": "string",
  "organizer_email": "string",
  "organizer_phone": "string",
  "schedule": [
    {
      "title": "string",
      "speaker_name": "string",
      "description": "string",
      "start_time": "datetime",
      "end_time": "datetime"
    }
  ]
}
```

**Response:** Event object

#### Get Events

Get events with optional filtering.

**Endpoint:** `GET /events`

**Query Parameters:**
- `category` (string, optional): Comma-separated list of event categories
- `start_date` (datetime, optional): Filter events starting after this date
- `end_date` (datetime, optional): Filter events ending before this date
- `latitude` (number, optional): User's latitude for location-based filtering
- `longitude` (number, optional): User's longitude for location-based filtering
- `distance` (number, optional, default=10.0): Maximum distance in kilometers
- `free_only` (boolean, optional, default=false): Return only free events

**Response:** Array of Event objects

#### Get Event by ID

Get details of a specific event.

**Endpoint:** `GET /events/{event_id}`

**Path Parameters:**
- `event_id` (string, required): Event ID

**Response:** Event object

#### RSVP to Event

Mark attendance or interest in an event.

**Endpoint:** `POST /events/{event_id}/rsvp`

**Path Parameters:**
- `event_id` (string, required): Event ID

**Query Parameters:**
- `user_id` (string, required): User ID

**Request Body:**
```json
{
  "status": "attending"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "RSVP recorded"
}
```

#### Get Event Attendees

Get users who are attending or interested in an event.

**Endpoint:** `GET /events/{event_id}/attendees`

**Path Parameters:**
- `event_id` (string, required): Event ID

**Query Parameters:**
- `status` (string, optional): Filter by RSVP status (e.g., "attending")

**Response:** Array of User objects

#### Get Event Recommendations

Get personalized event recommendations for a user.

**Endpoint:** `GET /events/recommendations/{user_id}`

**Path Parameters:**
- `user_id` (string, required): User ID

**Query Parameters:**
- `latitude` (number, required): User's current latitude
- `longitude` (number, required): User's current longitude
- `distance` (number, optional, default=10.0): Maximum distance in kilometers

**Response:** Array of Event objects

---

### Connections

#### Send Connection Request

Send a connection request to another user.

**Endpoint:** `POST /connections/request`

**Request Body:**
```json
{
  "from_user_id": "string",
  "to_user_id": "string"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Connection request sent",
  "connection_id": "string"
}
```

#### Respond to Connection Request

Accept or decline a connection request.

**Endpoint:** `POST /connections/respond/find`

**Request Body:**
```json
{
  "request_id": "string",  // ID of the user who sent the request
  "user_id": "string",     // ID of the user responding
  "status": "string"       // "accept" or "decline"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Connection request accepted/declined"
}
```

#### Get User Connections

Get a user's connections.

**Endpoint:** `GET /connections/user/{user_id}`

**Path Parameters:**
- `user_id` (string, required): User ID

**Query Parameters:**
- `status` (string, optional): Filter by connection status (e.g., "pending", "accepted")

**Response:** Array of Connection objects

#### Get Connection Recommendations

Get personalized connection recommendations for a user.

**Endpoint:** `GET /connections/recommendations/{user_id}`

**Path Parameters:**
- `user_id` (string, required): User ID

**Query Parameters:**
- `limit` (integer, optional, default=10): Maximum number of recommendations to return

**Response:** Array of User objects

#### Get Event-Based Connection Recommendations

Get connection recommendations for a user at a specific event.

**Endpoint:** `GET /connections/event/{event_id}/user/{user_id}`

**Path Parameters:**
- `event_id` (string, required): Event ID
- `user_id` (string, required): User ID

**Query Parameters:**
- `limit` (integer, optional, default=10): Maximum number of recommendations to return

**Response:** Array of User objects

---

### Preferences

#### Set User Preferences

Set a user's preferences for notifications, privacy, etc.

**Endpoint:** `POST /preferences/{user_id}`

**Path Parameters:**
- `user_id` (string, required): User ID

**Request Body:**
```json
{
  "notification_events": boolean,
  "notification_connections": boolean,
  "notification_messages": boolean,
  "privacy_profile": "string",  // "public", "private", "friends-only"
  "timezone": "string"
}
```

**Response:** Preferences object

#### Get User Preferences

Get a user's preferences.

**Endpoint:** `GET /preferences/{user_id}`

**Path Parameters:**
- `user_id` (string, required): User ID

**Response:** Preferences object

#### Update User Preferences

Update a user's preferences.

**Endpoint:** `PUT /preferences/{user_id}`

**Path Parameters:**
- `user_id` (string, required): User ID

**Request Body:** Same as Set User Preferences (partial updates supported)

**Response:** Updated Preferences object

---

### Feedback

#### Create Feedback

Submit feedback for an event.

**Endpoint:** `POST /feedback/{event_id}`

**Path Parameters:**
- `event_id` (string, required): Event ID

**Query Parameters:**
- `user_id` (string, required): User ID

**Request Body:**
```json
{
  "rating": integer,  // 1-5
  "comment": "string"
}
```

**Response:**
```json
{
  "id": "string",
  "event_id": "string",
  "user_id": "string",
  "rating": integer,
  "comment": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Get All Event Feedback

Get all feedback for an event.

**Endpoint:** `GET /feedback/{event_id}`

**Path Parameters:**
- `event_id` (string, required): Event ID

**Response:** Array of Feedback objects

#### Get User Feedback for Event

Get a specific user's feedback for an event.

**Endpoint:** `GET /feedback/{event_id}/user/{user_id}`

**Path Parameters:**
- `event_id` (string, required): Event ID
- `user_id` (string, required): User ID

**Response:** Feedback object

#### Get All User Feedback

Get all feedback submitted by a user.

**Endpoint:** `GET /feedback/user/{user_id}`

**Path Parameters:**
- `user_id` (string, required): User ID

**Response:** Array of Feedback objects

#### Update Feedback

Update existing feedback.

**Endpoint:** `PUT /feedback/{event_id}/user/{user_id}`

**Path Parameters:**
- `event_id` (string, required): Event ID
- `user_id` (string, required): User ID

**Request Body:**
```json
{
  "rating": integer,
  "comment": "string"
}
```

**Response:** Updated Feedback object

#### Delete Feedback

Delete feedback.

**Endpoint:** `DELETE /feedback/{event_id}/user/{user_id}`

**Path Parameters:**
- `event_id` (string, required): Event ID
- `user_id` (string, required): User ID

**Response:**
```json
{
  "status": "success",
  "message": "Feedback deleted"
}
```

## Data Models

### User Model
```json
{
  "id": "string",
  "uid": "string",
  "display_name": "string",
  "email": "string",
  "bio": "string",
  "profile_image_url": "string",
  "interests": ["string"],
  "location": {
    "latitude": number,
    "longitude": number
  },
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Event Model
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "start_time": "datetime",
  "end_time": "datetime",
  "venue": {
    "name": "string",
    "address": "string",
    "latitude": number,
    "longitude": number
  },
  "category": ["string"],
  "image_url": "string",
  "price": number,
  "organizer_name": "string",
  "organizer_email": "string",
  "organizer_phone": "string",
  "schedule": [
    {
      "title": "string",
      "speaker_name": "string",
      "description": "string",
      "start_time": "datetime",
      "end_time": "datetime"
    }
  ],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Connection Model
```json
{
  "id": "string",
  "from_user_id": "string",
  "to_user_id": "string",
  "status": "string",  // "pending", "accepted", "declined"
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Feedback Model
```json
{
  "id": "string",
  "event_id": "string",
  "user_id": "string",
  "rating": integer,  // 1-5
  "comment": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Preferences Model
```json
{
  "user_id": "string",
  "notification_events": boolean,
  "notification_connections": boolean,
  "notification_messages": boolean,
  "privacy_profile": "string",  // "public", "private", "friends-only"
  "timezone": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Status Codes

- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error