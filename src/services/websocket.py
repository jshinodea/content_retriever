"""
WebSocket Manager Module

This module handles WebSocket connections and message processing for real-time communication.
"""

from typing import Dict

from fastapi import WebSocket
from pydantic import ValidationError

from models.content import DialogueMessage

class WebSocketManager:
    """Manages WebSocket connections and message handling."""
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_states: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_states[client_id] = {"last_message": None}
    
    async def disconnect(self, client_id: str):
        """Handle client disconnection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_states:
            del self.client_states[client_id]
    
    async def send_message(self, client_id: str, message: str):
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        for connection in self.active_connections.values():
            await connection.send_text(message)
    
    async def process_message(self, client_id: str, message: str) -> str:
        """Process incoming messages from clients."""
        try:
            # Parse the message into a DialogueMessage
            dialogue_msg = DialogueMessage.model_validate_json(message)
            
            # Store the message in client state
            self.client_states[client_id]["last_message"] = dialogue_msg
            
            # TODO: Implement message processing logic based on message_type
            # For now, just echo the message back
            response = DialogueMessage(
                sender="agent",
                message=f"Received: {dialogue_msg.message}",
                message_type="response",
                requires_response=False
            )
            
            return response.model_dump_json()
            
        except ValidationError as e:
            error_msg = DialogueMessage(
                sender="agent",
                message=f"Invalid message format: {str(e)}",
                message_type="error",
                requires_response=False
            )
            return error_msg.model_dump_json()
        except Exception as e:
            error_msg = DialogueMessage(
                sender="agent",
                message=f"Error processing message: {str(e)}",
                message_type="error",
                requires_response=False
            )
            return error_msg.model_dump_json() 