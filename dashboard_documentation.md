# Dashboard API Documentation

## Endpoints

### Get Comprehensive Event Details

Get detailed information about an event including full event information, attendee profiles, and feedback with ratings.

**Endpoint:** `GET /dashboard/{event_id}/comprehensive`

**Path Parameters:**
- `event_id` (string, required): ID of the event to get comprehensive details for

**Response:**
```json
{
  "event": {
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
  },
  "attendees": {
    "count": integer,
    "list": [
      {
        "user_id": "string",
        "display_name": "string",
        "profile_image_url": "string",
        "email": "string",
        "rsvp_date": "datetime"
      }
    ]
  },
  "feedback": {
    "count": integer,
    "average_rating": number,
    "list": [
      {
        "id": "string",
        "event_id": "string",
        "user_id": "string",
        "rating": integer,
        "comment": "string",
        "created_at": "datetime",
        "updated_at": "datetime",
        "user": {
          "user_id": "string",
          "display_name": "string",
          "profile_image_url": "string"
        }
      }
    ]
  }
}
```

### Get Organizer Dashboard

Get summary details for all events organized by a specific email address, including statistics and event listings.

**Endpoint:** `GET /dashboard/organizer/{email}`

**Path Parameters:**
- `email` (string, required): Email of the organizer to fetch events for

**Response:**
```json
{
  "organizer_email": "string",
  "stats": {
    "total_events": integer,
    "total_attendees": integer,
    "average_rating": number
  },
  "upcoming_events": [
    {
      "id": "string",
      "title": "string",
      "start_time": "datetime",
      "venue": "string",
      "attendees_count": integer
    }
  ],
  "past_events": [
    {
      "id": "string",
      "title": "string",
      "start_time": "datetime",
      "venue": "string",
      "attendees_count": integer
    }
  ]
}
```

### Get Event Attendees Details

Get a simplified list of attendee details for an event.

**Endpoint:** `GET /dashboard/{event_id}/attendees`

**Path Parameters:**
- `event_id` (string, required): ID of the event to get attendee details for

**Response:**
```json
{
  "event_id": "string",
  "attendees_count": integer,
  "attendees": [
    {
      "display_name": "string",
      "profile_image_url": "string",
      "email": "string",
      "rsvp_date": "datetime"
    }
  ]
}
```

### Get Event Feedback With User Details

Get all feedback for an event with enriched user information.

**Endpoint:** `GET /dashboard/{event_id}/feedback`

**Path Parameters:**
- `event_id` (string, required): ID of the event to get feedback for

**Response:**
```json
{
  "event_id": "string",
  "feedback_count": integer,
  "average_rating": number,
  "feedback": [
    {
      "id": "string",
      "event_id": "string",
      "user_id": "string",
      "rating": integer,
      "comment": "string",
      "created_at": "datetime",
      "updated_at": "datetime",
      "user": {
        "user_id": "string",
        "display_name": "string",
        "profile_image_url": "string"
      }
    }
  ]
}
```

## Status Codes

- 200: Success - The request was successful
- 404: Not Found - Event or organizer not found
- 500: Internal Server Error - Server-side error occurred