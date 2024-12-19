# Integration Test Suite
#------------------

# Description: End-to-end tests for the content retrieval system
# Dependencies: pytest, pytest-asyncio, pytest-aiohttp
# Author: AI Agent
# Last Modified: 2024-01-09

import json
import uuid
from typing import Dict, List

import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from core.config import settings
from main import app
from models.content import ContentField, ContentRequest, ContentResponse, ContentTable
from services.agent import ContentAgent
from services.database import DatabaseService
from services.llm import LLMService
from services.scraper import WebScraper
from services.search import SearchService
from services.vision import VisionService
from services.websocket import WebSocketManager

# Test client setup
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_url():
    return "https://example.com/test"

@pytest.fixture
def test_instructions():
    return "Extract the main article content and author information"

@pytest.fixture
async def database():
    """Initialize test database"""
    db = DatabaseService()
    yield db
    await db.close()

@pytest.fixture
def websocket_manager():
    return WebSocketManager()

@pytest.fixture
def content_agent():
    return ContentAgent()

# Test complete content retrieval workflow
@pytest.mark.asyncio
async def test_content_retrieval_workflow(
    client,
    test_url,
    test_instructions,
    database,
    websocket_manager,
    content_agent
):
    # 1. Start content retrieval task
    task_id = uuid.uuid4()
    request = ContentRequest(
        url=test_url,
        instructions=test_instructions
    )
    
    response = await content_agent.process_task(request)
    assert response.task_id == task_id
    assert response.status == "completed"
    
    # 2. Verify task stored in database
    task = await database.get_task(task_id)
    assert task is not None
    assert task["url"] == test_url
    assert task["instructions"] == test_instructions
    
    # 3. Check content items stored
    items = await database.get_content_items(task_id)
    assert len(items) > 0
    
    # 4. Verify content table
    table = await database.get_content_table(task_id)
    assert table is not None
    assert len(table.columns) > 0
    assert len(table.rows) > 0

# Test WebSocket communication
@pytest.mark.asyncio
async def test_websocket_communication(
    client,
    websocket_manager
):
    client_id = "test_client"
    
    # Connect WebSocket client
    with client.websocket_connect(f"/ws/{client_id}") as websocket:
        # Send test message
        test_message = {
            "type": "user_message",
            "content": "Test message"
        }
        await websocket.send_json(test_message)
        
        # Receive response
        response = await websocket.receive_json()
        assert response["type"] == "agent_message"
        assert "content" in response

# Test error handling
@pytest.mark.asyncio
async def test_error_handling(
    client,
    test_url,
    test_instructions,
    content_agent
):
    # Test invalid URL
    request = ContentRequest(
        url="invalid_url",
        instructions=test_instructions
    )
    
    with pytest.raises(ValueError):
        await content_agent.process_task(request)
    
    # Test missing instructions
    request = ContentRequest(
        url=test_url,
        instructions=""
    )
    
    with pytest.raises(ValueError):
        await content_agent.process_task(request)

# Test content processing
@pytest.mark.asyncio
async def test_content_processing(
    content_agent,
    test_url,
    test_instructions
):
    # Test content extraction
    request = ContentRequest(
        url=test_url,
        instructions=test_instructions
    )
    
    response = await content_agent.process_task(request)
    assert response.content is not None
    
    # Verify content structure
    assert isinstance(response.content, List)
    for item in response.content:
        assert isinstance(item, Dict)
        for field in item.values():
            assert isinstance(field, ContentField)

# Test database operations
@pytest.mark.asyncio
async def test_database_operations(database):
    # Test task storage
    task_id = uuid.uuid4()
    await database.store_task(
        task_id=task_id,
        url="https://example.com",
        instructions="Test instructions",
        status="completed"
    )
    
    # Verify task retrieval
    task = await database.get_task(task_id)
    assert task is not None
    assert task["status"] == "completed"
    
    # Test content storage
    items = [
        {
            "title": ContentField(
                name="title",
                value="Test Title",
                type="text",
                source="webpage"
            )
        }
    ]
    await database.store_content_items(task_id, items)
    
    # Verify content retrieval
    stored_items = await database.get_content_items(task_id)
    assert len(stored_items) == 1
    assert stored_items[0]["title"].value == "Test Title"

# Test content table operations
@pytest.mark.asyncio
async def test_content_table_operations(database):
    task_id = uuid.uuid4()
    
    # Create test table
    table = ContentTable(
        columns=["title", "author"],
        rows=[
            {"title": "Test Title", "author": "Test Author"}
        ],
        metadata={"source": "test"}
    )
    
    # Store table
    await database.store_content_table(task_id, table)
    
    # Retrieve and verify table
    stored_table = await database.get_content_table(task_id)
    assert stored_table is not None
    assert stored_table.columns == table.columns
    assert len(stored_table.rows) == 1
    assert stored_table.rows[0]["title"] == "Test Title"

# Test API endpoints
def test_api_endpoints(client):
    # Test health check
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    
    # Test task creation
    task_data = {
        "url": "https://example.com",
        "instructions": "Test instructions"
    }
    response = client.post("/task", json=task_data)
    assert response.status_code == 200
    assert "task_id" in response.json()

# Test WebSocket manager
@pytest.mark.asyncio
async def test_websocket_manager(websocket_manager):
    client_id = "test_client"
    
    # Test client connection
    await websocket_manager.connect(client_id, WebSocket)
    assert client_id in websocket_manager.active_connections
    
    # Test message broadcasting
    test_message = {"type": "test", "content": "Test message"}
    await websocket_manager.broadcast(test_message)
    
    # Test client disconnection
    await websocket_manager.disconnect(client_id)
    assert client_id not in websocket_manager.active_connections 