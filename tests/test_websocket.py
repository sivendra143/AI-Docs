"""
WebSocket test suite for AI Document Chat application.
Tests WebSocket connections, message handling, and real-time updates.
"""
import os
import sys
import json
import time
import asyncio
import pytest
import websockets
from pathlib import Path
from typing import Dict, Any, Optional, AsyncGenerator

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test configuration
TEST_CONFIG = {
    "host": "localhost",
    "port": 5000,
    "ws_uri": "ws://localhost:5000/ws",
    "test_user": "test_user",
    "test_conversation_id": "test_conv_123"
}

# Test messages
TEST_MESSAGES = [
    {"type": "message", "content": "Hello, how are you?"},
    {"type": "question", "content": "What is this document about?"},
    {"type": "command", "command": "clear_history"}
]

class WebSocketTestClient:
    """WebSocket test client for testing WebSocket endpoints."""
    
    def __init__(self, uri: str):
        self.uri = uri
        self.websocket = None
        self.received_messages = []
    
    async def connect(self):
        """Establish WebSocket connection."""
        self.websocket = await websockets.connect(self.uri)
        return self.websocket
    
    async def send(self, message: Dict[str, Any]):
        """Send a JSON message through the WebSocket."""
        if not self.websocket:
            await self.connect()
        await self.websocket.send(json.dumps(message))
    
    async def receive(self) -> Dict[str, Any]:
        """Receive and parse a JSON message from the WebSocket."""
        if not self.websocket:
            raise RuntimeError("WebSocket not connected")
        
        message = await self.websocket.recv()
        try:
            data = json.loads(message)
            self.received_messages.append(data)
            return data
        except json.JSONDecodeError:
            return {"type": "error", "message": "Invalid JSON received"}
    
    async def close(self):
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

@pytest.fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def websocket_client() -> AsyncGenerator[WebSocketTestClient, None]:
    """Create a WebSocket test client."""
    client = WebSocketTestClient(TEST_CONFIG["ws_uri"])
    await client.connect()
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_websocket_connection(websocket_client: WebSocketTestClient):
    """Test WebSocket connection establishment."""
    assert websocket_client.websocket is not None
    assert websocket_client.websocket.open
    
    # Test ping/pong
    pong_waiter = await websocket_client.websocket.ping()
    await pong_waiter  # Will raise an exception if no pong received

@pytest.mark.asyncio
async def test_authentication(websocket_client: WebSocketTestClient):
    """Test WebSocket authentication."""
    # Send authentication message
    auth_message = {
        "type": "auth",
        "user_id": TEST_CONFIG["test_user"],
        "conversation_id": TEST_CONFIG["test_conversation_id"]
    }
    
    await websocket_client.send(auth_message)
    response = await websocket_client.receive()
    
    assert response["type"] == "auth_response"
    assert response["status"] == "success"
    assert response["user_id"] == TEST_CONFIG["test_user"]
    assert response["conversation_id"] == TEST_CONFIG["test_conversation_id"]

@pytest.mark.asyncio
async def test_message_exchange(websocket_client: WebSocketTestClient):
    """Test sending and receiving messages through WebSocket."""
    # First authenticate
    await websocket_client.send({
        "type": "auth",
        "user_id": TEST_CONFIG["test_user"],
        "conversation_id": TEST_CONFIG["test_conversation_id"]
    })
    await websocket_client.receive()  # Discard auth response
    
    # Test text message
    test_message = {"type": "message", "content": "Hello, WebSocket!"}
    await websocket_client.send(test_message)
    
    # Should receive a typing indicator first
    typing_response = await websocket_client.receive()
    assert typing_response["type"] == "typing"
    assert typing_response["status"] == "started"
    
    # Then the actual response
    response = await websocket_client.receive()
    assert response["type"] == "message"
    assert "content" in response
    assert "Hello, WebSocket!" in response["content"]
    
    # Then typing stopped
    typing_stopped = await websocket_client.receive()
    assert typing_stopped["type"] == "typing"
    assert typing_stopped["status"] == "stopped"

@pytest.mark.asyncio
async def test_conversation_management(websocket_client: WebSocketTestClient):
    """Test conversation management through WebSocket."""
    # Authenticate
    await websocket_client.send({
        "type": "auth",
        "user_id": TEST_CONFIG["test_user"],
        "conversation_id": TEST_CONFIG["test_conversation_id"]
    })
    await websocket_client.receive()  # Discard auth response
    
    # Test getting conversation history
    await websocket_client.send({"type": "get_history"})
    response = await websocket_client.receive()
    assert response["type"] == "history"
    assert isinstance(response.get("messages", []), list)
    
    # Test clearing conversation
    await websocket_client.send({"type": "clear_history"})
    response = await websocket_client.receive()
    assert response["type"] == "status"
    assert response["status"] == "success"
    assert "history cleared" in response.get("message", "").lower()

@pytest.mark.asyncio
async def test_error_handling(websocket_client: WebSocketTestClient):
    """Test WebSocket error handling."""
    # Test invalid message format
    await websocket_client.websocket.send("invalid json")
    response = await websocket_client.receive()
    assert response["type"] == "error"
    assert "invalid json" in response.get("message", "").lower()
    
    # Test invalid message type
    await websocket_client.send({"type": "invalid_type"})
    response = await websocket_client.receive()
    assert response["type"] == "error"
    assert "unsupported message type" in response.get("message", "").lower()

@pytest.mark.asyncio
async def test_binary_messages(websocket_client: WebSocketTestClient):
    """Test handling of binary messages."""
    # Test sending binary data (should be rejected)
    binary_data = b"\x00\x01\x02\x03"
    await websocket_client.websocket.send(binary_data)
    response = await websocket_client.receive()
    assert response["type"] == "error"
    assert "binary data not supported" in response.get("message", "").lower()

@pytest.mark.asyncio
async def test_concurrent_connections():
    """Test multiple concurrent WebSocket connections."""
    num_clients = 3
    clients = []
    
    try:
        # Create multiple clients
        for i in range(num_clients):
            client = WebSocketTestClient(TEST_CONFIG["ws_uri"])
            await client.connect()
            await client.send({
                "type": "auth",
                "user_id": f"user_{i}",
                "conversation_id": f"conv_{i}"
            })
            await client.receive()  # Discard auth response
            clients.append(client)
        
        # Send messages from all clients
        for i, client in enumerate(clients):
            await client.send({
                "type": "message",
                "content": f"Hello from client {i}"
            })
        
        # Verify responses
        for i, client in enumerate(clients):
            # Typing started
            typing = await client.receive()
            assert typing["type"] == "typing"
            assert typing["status"] == "started"
            
            # Message response
            response = await client.receive()
            assert response["type"] == "message"
            assert f"client {i}" in response["content"].lower()
            
            # Typing stopped
            typing_stopped = await client.receive()
            assert typing_stopped["type"] == "typing"
            assert typing_stopped["status"] == "stopped"
            
    finally:
        # Clean up
        for client in clients:
            await client.close()

if __name__ == "__main__":
    # Run tests directly with: python -m tests.test_websocket
    import pytest
    import sys
    sys.exit(pytest.main(["-v", __file__]))
