"""
API Routes Module

This module defines the FastAPI routes for the content retrieval system.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from models.content import ContentRequest, ContentResponse
from services.agent import ContentAgent
from services.websocket import WebSocketManager

router = APIRouter()
ws_manager = WebSocketManager()

# Mount static files
static_path = Path(__file__).parent.parent / "frontend" / "static"
router.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@router.get("/")
async def get_index():
    """Serve the main HTML page."""
    return FileResponse(str(static_path / "index.html"))

class TaskRequest(BaseModel):
    """Content retrieval task request model."""
    url: HttpUrl
    instructions: str

@router.post("/task", response_model=ContentResponse)
async def create_task(request: TaskRequest):
    """Create a new content retrieval task."""
    try:
        agent = ContentAgent()
        response = await agent.process_task(
            url=str(request.url),
            instructions=request.instructions
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication."""
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Process the received message
            response = await ws_manager.process_message(client_id, data)
            await websocket.send_text(response)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(client_id)

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 