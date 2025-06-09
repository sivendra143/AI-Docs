"""
Tests for the Flask application routes and WebSocket handlers.
"""
import os
import sys
import json
import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app import create_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })
    
    # Mock the extensions
    app.extensions = {
        'document_processor': MagicMock(),
        'chatbot': MagicMock(),
        'conversation_manager': MagicMock()
    }
    
    return app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

def test_index_route(client):
    """Test the index route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'AI Document Chat' in response.data

def test_upload_route(client, tmp_path):
    """Test the file upload route."""
    # Create a test file
    test_file = tmp_path / 'test.txt'
    test_file.write_text('Test file content')
    
    # Mock the document processor
    with open(test_file, 'rb') as f:
        response = client.post('/upload', data={
            'file': (f, 'test.txt')
        }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'File uploaded successfully' in data['message']

@pytest.mark.asyncio
async def test_websocket_connection(websocket_client):
    """Test WebSocket connection and authentication."""
    # Test connection
    assert websocket_client.websocket is not None
    assert websocket_client.websocket.open
    
    # Test authentication
    auth_message = {
        "type": "auth",
        "user_id": "test_user",
        "conversation_id": "test_conv"
    }
    await websocket_client.send(auth_message)
    
    response = await websocket_client.receive()
    assert response["type"] == "auth_response"
    assert response["status"] == "success"

@pytest.mark.asyncio
async def test_websocket_message(websocket_client, app):
    """Test sending and receiving messages through WebSocket."""
    # Mock the chatbot response
    mock_response = {
        "answer": "Test response",
        "sources": ["test.pdf"],
        "suggested_questions": ["What is this about?"]
    }
    
    app.extensions['chatbot'].ask = AsyncMock(return_value=mock_response)
    
    # Authenticate
    await websocket_client.send({
        "type": "auth",
        "user_id": "test_user",
        "conversation_id": "test_conv"
    })
    await websocket_client.receive()  # Discard auth response
    
    # Send a message
    test_message = {
        "type": "message",
        "content": "Hello, test!"
    }
    await websocket_client.send(test_message)
    
    # Verify typing indicator
    typing_response = await websocket_client.receive()
    assert typing_response["type"] == "typing"
    assert typing_response["status"] == "started"
    
    # Verify message response
    response = await websocket_client.receive()
    assert response["type"] == "message"
    assert response["content"] == "Test response"
    assert response["sources"] == ["test.pdf"]
    assert "suggested_questions" in response
    
    # Verify typing stopped
    typing_stopped = await websocket_client.receive()
    assert typing_stopped["type"] == "typing"
    assert typing_stopped["status"] == "stopped"

@pytest.mark.asyncio
async def test_websocket_get_history(websocket_client, app):
    """Test getting conversation history through WebSocket."""
    # Mock conversation history
    mock_history = [
        {"role": "user", "content": "Hello", "timestamp": "2023-01-01T00:00:00"},
        {"role": "assistant", "content": "Hi there!", "timestamp": "2023-01-01T00:00:01"}
    ]
    
    app.extensions['conversation_manager'].get_conversation_history.return_value = mock_history
    
    # Authenticate
    await websocket_client.send({
        "type": "auth",
        "user_id": "test_user",
        "conversation_id": "test_conv"
    })
    await websocket_client.receive()  # Discard auth response
    
    # Request history
    await websocket_client.send({"type": "get_history"})
    
    # Verify history response
    response = await websocket_client.receive()
    assert response["type"] == "history"
    assert len(response["messages"]) == 2
    assert response["messages"] == mock_history

@pytest.mark.asyncio
async def test_websocket_clear_history(websocket_client, app):
    """Test clearing conversation history through WebSocket."""
    # Authenticate
    await websocket_client.send({
        "type": "auth",
        "user_id": "test_user",
        "conversation_id": "test_conv"
    })
    await websocket_client.receive()  # Discard auth response
    
    # Clear history
    await websocket_client.send({"type": "clear_history"})
    
    # Verify clear history response
    response = await websocket_client.receive()
    assert response["type"] == "status"
    assert response["status"] == "success"
    assert "history cleared" in response["message"].lower()
    
    # Verify the clear method was called
    app.extensions['conversation_manager'].clear_conversation.assert_called_once_with(
        "test_user", "test_conv"
    )

def test_health_check_route(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'

@patch('src.app.DocumentProcessor')
def test_process_documents_route(mock_dp, client):
    """Test the process documents endpoint."""
    # Mock the document processor
    mock_processor = MagicMock()
    mock_processor.process_documents = AsyncMock(return_value={"status": "success"})
    mock_dp.return_value = mock_processor
    
    response = client.post('/api/process-documents')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'

@patch('src.app.ChatbotLLM')
def test_ask_question_route(mock_chatbot, client):
    """Test the ask question endpoint."""
    # Mock the chatbot response
    mock_response = {
        "answer": "Test response",
        "sources": ["test.pdf"],
        "suggested_questions": ["What is this about?"]
    }
    
    mock_chatbot.return_value.ask = AsyncMock(return_value=mock_response)
    
    response = client.post('/api/ask', json={"question": "Test question"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['answer'] == "Test response"
    assert data['sources'] == ["test.pdf"]

def test_404_error_handler(client):
    """Test 404 error handling."""
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Not Found' in data['error']

def test_500_error_handler(client, app):
    """Test 500 error handling."""
    # Create a route that will raise an exception
    @app.route('/test-error')
    def test_error():
        raise Exception('Test error')
    
    # Test the error handler
    response = client.get('/test-error')
    assert response.status_code == 500
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Internal Server Error' in data['error']
