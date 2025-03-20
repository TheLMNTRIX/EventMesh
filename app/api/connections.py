from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from app.models.connection import ConnectionRequest, ConnectionResponse, ConnectionSuggestion, ConnectionRecommendation
from app.services.firebase_service import firebase_service
from app.services.recommendation_service import recommendation_service
from app.utils.validators import validate_connection_status
from app.models.connection import ConnectionRecommendation
from app.services.recommendation_service import recommendation_service


router = APIRouter()

# Update the request endpoint
@router.post("/request")
async def create_connection_request(request: ConnectionRequest):
    """Send a connection request to another user"""
    # Check if users exist
    from_user = await firebase_service.get_user(request.from_user_id)
    if not from_user:
        raise HTTPException(status_code=404, detail="Requesting user not found")
    
    to_user = await firebase_service.get_user(request.to_user_id)
    if not to_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    
    # Check if request already exists
    existing_connections = await firebase_service.get_user_connections(request.from_user_id)
    for conn in existing_connections:
        if (conn["from_user_id"] == request.from_user_id and conn["to_user_id"] == request.to_user_id) or \
           (conn["from_user_id"] == request.to_user_id and conn["to_user_id"] == request.from_user_id):
            return {
                "status": "exists",
                "message": "Connection already exists or is pending",
                "connection_id": conn["id"],
                "connection_status": conn["status"]
            }
    
    # Create connection request
    connection = await firebase_service.create_connection_request(request.from_user_id, request.to_user_id)
    
    return {
        "status": "success",
        "message": "Connection request sent",
        "connection_id": connection["id"]
    }

# Modify the respond endpoint
@router.post("/respond/{connection_id}")
async def respond_to_connection_request(
    connection_id: str, 
    response: ConnectionResponse
):
    """Accept or decline a connection request"""
    # Validate response
    if response.status not in ["accept", "decline"]:
        raise HTTPException(status_code=400, detail="Invalid response status")
    
    # Get existing connections for the responding user
    existing_connections = await firebase_service.get_user_connections(response.user_id)
    
    # Find the connection between the sender and receiver
    connection = next((
        conn for conn in existing_connections 
        if (conn["to_user_id"] == response.user_id and conn["from_user_id"] == response.request_id) or
            (conn["from_user_id"] == response.user_id and conn["to_user_id"] == response.request_id)
    ), None)
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection request not found")
    
    # Verify the responding user is the recipient of the request
    if connection["to_user_id"] != response.user_id:
        raise HTTPException(status_code=403, detail="Only the recipient can respond to this request")
    
    # Map response to connection status
    status_map = {
        "accept": "accepted",
        "decline": "declined"
    }
    
    try:
        # Get the actual connection_id from the found connection document
        actual_connection_id = connection["id"]
        
        if response.status == "accept":
            # Update connection status
            updated_connection = await firebase_service.update_connection_status(actual_connection_id, status_map[response.status])
            
            from_user_id = updated_connection["from_user_id"]
            to_user_id = updated_connection["to_user_id"]
            
            # Ensure both users exist and get their current connection counts
            from_user = await firebase_service.get_user(from_user_id)
            to_user = await firebase_service.get_user(to_user_id)
            
            if from_user and to_user:
                # Update connection counts
                from_count = from_user.get("connection_count", 0) + 1
                to_count = to_user.get("connection_count", 0) + 1
                
                # Add connections array if it doesn't exist
                from_connections = from_user.get("connections", [])
                to_connections = to_user.get("connections", [])
                
                # Add user IDs to the connections array if not already there
                if to_user_id not in from_connections:
                    from_connections.append(to_user_id)
                
                if from_user_id not in to_connections:
                    to_connections.append(from_user_id)
                
                # Update both users with connection count and connections array
                await firebase_service.update_user(from_user_id, {
                    "connection_count": from_count,
                    "connections": from_connections
                })
                
                await firebase_service.update_user(to_user_id, {
                    "connection_count": to_count,
                    "connections": to_connections
                })
                
                print(f"Updated connections arrays - From: {from_user_id} ({from_connections}), To: {to_user_id} ({to_connections})")
            
        else:  # Decline request
            # Delete the connection document instead of updating status
            connection_ref = firebase_service.db.collection('connections').document(actual_connection_id)
            connection_ref.delete()
            print(f"Deleted connection request {actual_connection_id}")
        
        return {
            "status": "success",
            "message": f"Connection request {response.status}ed",
            "connection_id": actual_connection_id
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Connection request not found: {str(e)}")

@router.get("/user/{user_id}")
async def get_user_connections(
    user_id: str,
    status: Optional[str] = Query(None, description="Filter by status: pending, accepted, declined, blocked")
):
    """Get all connections for a user"""
    # Validate user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate status if provided
    if status and not validate_connection_status(status):
        raise HTTPException(status_code=400, detail="Invalid connection status")
    
    # Get connections
    connections = await firebase_service.get_user_connections(user_id, status)
    
    # Enrich with user details
    enriched_connections = []
    for conn in connections:
        # Determine the other user in the connection
        other_user_id = conn["to_user_id"] if conn["from_user_id"] == user_id else conn["from_user_id"]
        other_user = await firebase_service.get_user(other_user_id)
        
        if other_user:
            enriched_conn = {
                "connection_id": conn["id"],
                "status": conn["status"],
                "created_at": conn["created_at"],
                "updated_at": conn.get("updated_at"),
                "is_outgoing": conn["from_user_id"] == user_id,
                "user": {
                    "uid": other_user["uid"],
                    "display_name": other_user.get("display_name", "Unknown"),
                    "profile_image_url": other_user.get("profile_image_url"),
                    "bio": other_user.get("bio")
                }
            }
            enriched_connections.append(enriched_conn)
    
    return enriched_connections




@router.get("/pending-requests")
async def get_pending_connection_requests(user_id: str = Query(..., description="ID of the user to check pending requests for")):
    """
    Get all pending connection requests sent to a user
    
    Returns: List of users who have sent pending connection requests to this user
    """
    # Validate user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all connections for the user
    all_connections = await firebase_service.get_user_connections(user_id)
    
    # Filter for incoming requests that are pending
    pending_requests = [
        conn for conn in all_connections 
        if conn["to_user_id"] == user_id and conn["status"] == "pending"
    ]
    
    # Get sender details for each pending request
    pending_senders = []
    for request in pending_requests:
        sender_id = request["from_user_id"]
        sender = await firebase_service.get_user(sender_id)
        
        if sender:
            pending_senders.append({
                "connection_id": request["id"],
                "uid": sender.get("uid"),
                "display_name": sender.get("display_name", "Unknown"),
                "email": sender.get("email", ""),
                "profile_image_url": sender.get("profile_image_url"),
                "created_at": request.get("created_at")
            })
    
    return pending_senders

@router.get("/recommendations/{user_id}", response_model=List[ConnectionRecommendation])
async def get_connection_recommendations(
    user_id: str,
    limit: int = Query(10, le=50, description="Maximum number of recommendations to return")
):
    """
    Get personalized connection recommendations for a user
    
    This endpoint suggests other users to connect with based on:
    - Mutual interests
    - Mutual connections
    - Events in common
    
    Returns connections with a score indicating relevance.
    """
    # Validate user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get recommendations from the recommendation service
    recommendations = await recommendation_service.get_connection_recommendations(
        user_id=user_id,
        limit=limit
    )
    
    # The recommendations already include score from your recommendation service
    return recommendations

@router.get("/event/{event_id}/user/{user_id}", response_model=List[ConnectionRecommendation])
async def get_event_based_connection_recommendations(
    event_id: str,
    user_id: str,
    limit: int = Query(10, le=50, description="Maximum number of recommendations to return")
):
    """
    Get connection recommendations for a user at a specific event
    
    This endpoint suggests other event attendees to connect with based on:
    - Mutual interests, especially those related to the event
    - Mutual connections
    
    Returns connections with a score indicating relevance.
    """
    # Validate user exists
    user = await firebase_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate event exists
    event = await firebase_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get recommendations from the recommendation service
    recommendations = await recommendation_service.get_event_based_connection_recommendations(
        event_id=event_id,
        user_id=user_id,
        limit=limit
    )
    
    # The recommendations already include score from your recommendation service
    return recommendations


__all__ = ["router"]