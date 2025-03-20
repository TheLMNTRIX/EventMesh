from fastapi import APIRouter, HTTPException, Depends
from app.services.firebase_service import firebase_service

router = APIRouter()

@router.post("/recalculate-counts")
async def recalculate_counts():
    """Admin endpoint to recalculate all counts"""
    await firebase_service.recalculate_counts()
    return {"status": "success", "message": "All counts recalculated"}

@router.post("/update-connections-arrays")
async def update_connections_arrays():
    """Admin endpoint to update all users' connections arrays based on accepted connections"""
    updated_count = await firebase_service.update_connections_arrays()
    return {
        "status": "success", 
        "message": f"Updated connection arrays for {updated_count} users"
    }

@router.post("/migrate-data")
async def migrate_data():
    """Admin endpoint to migrate all data to new structure"""
    result = await firebase_service.migrate_data_structures()
    return {
        "status": "success",
        "message": "Data migration completed",
        "details": result
    }

@router.post("/recalculate-events-attended")
async def recalculate_events_attended():
    """Admin endpoint to recalculate all users' events_attended based on event RSVPs"""
    updated_count = await firebase_service.recalculate_events_attended()
    return {
        "status": "success", 
        "message": f"Updated events_attended for {updated_count} users"
    }