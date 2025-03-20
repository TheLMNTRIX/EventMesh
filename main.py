from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import users, events, connections, feedback, admin
from app.api.feedback import router as feedback_router
from app.api.dashboard import router as dashboard_router

app = FastAPI(
    title="EventMesh API",
    description="Backend API for EventMesh mobile application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(connections.router, prefix="/api/connections", tags=["Connections"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["feedback"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])

@app.get("/")
async def root():
    return {"message": "Welcome to EventMesh API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)