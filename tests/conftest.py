"""
Configuration and fixtures for pytest.
This file is automatically discovered by pytest and used to define fixtures and hooks.
"""
import os
import sys
import asyncio
import pytest
from pathlib import Path
from typing import Generator, AsyncGenerator

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure asyncio to use the same event loop for all tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Test configuration
@pytest.fixture(scope="session")
def test_config():
    """Load test configuration."""
    return {
        "host": "localhost",
        "port": 5000,
        "ws_uri": "ws://localhost:5000/ws",
        "test_user": "test_user",
        "test_conversation_id": "test_conv_123"
    }

# Async fixtures
@pytest.fixture
def anyio_backend():
    """Use asyncio as the default test runner."""
    return 'asyncio'

# Test client for the application
@pytest.fixture
async def async_client():
    """Create a test client for the application."""
    from src.app import create_app
    
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })
    
    async with app.test_client() as client:
        yield client

# WebSocket test client
@pytest.fixture
async def websocket_client(test_config) -> AsyncGenerator:
    """Create a WebSocket test client."""
    from tests.test_websocket import WebSocketTestClient
    
    client = WebSocketTestClient(test_config["ws_uri"])
    await client.connect()
    
    try:
        yield client
    finally:
        await client.close()

# Mock LLM for testing
@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    from unittest.mock import MagicMock
    
    mock = MagicMock()
    mock.ask.return_value = "This is a test response."
    mock.generate.return_value = {"answer": "This is a test response.", "sources": []}
    
    return mock

# Mock vector store for testing
@pytest.fixture
def mock_vector_store():
    """Create a mock vector store for testing."""
    from unittest.mock import MagicMock
    
    mock = MagicMock()
    mock.similarity_search.return_value = [
        {"page_content": "Test document content", "metadata": {"source": "test.pdf", "page": 1}}
    ]
    
    return mock

# Test document directory
@pytest.fixture(scope="session")
def test_docs_dir(tmp_path_factory):
    """Create a temporary directory for test documents."""
    docs_dir = tmp_path_factory.mktemp("test_docs")
    
    # Create a test document
    test_doc = docs_dir / "test.txt"
    test_doc.write_text("This is a test document for unit testing.")
    
    return str(docs_dir)

# Test configuration file
@pytest.fixture(scope="session")
def test_config_file(tmp_path_factory, test_docs_dir):
    """Create a test configuration file."""
    config = {
        "document_processor": {
            "docs_folder": test_docs_dir,
            "chunk_size": 1000,
            "chunk_overlap": 200
        },
        "llm": {
            "model_name": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "embedding": {
            "model_name": "all-MiniLM-L6-v2"
        },
        "vector_store": {
            "persist_directory": str(tmp_path_factory.mktemp("test_vector_store")),
            "index_name": "test_index"
        },
        "server": {
            "host": "localhost",
            "port": 5000,
            "debug": True
        },
        "ui": {
            "title": "AI Document Chat - Test",
            "description": "Test instance of AI Document Chat"
        }
    }
    
    config_path = tmp_path_factory.mktemp("config") / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f)
    
    return str(config_path)
