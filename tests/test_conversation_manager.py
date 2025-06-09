"""
Tests for the ConversationManager class.
"""
import os
import sys
import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from collections import deque

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.conversation_manager import ConversationManager

@pytest.fixture
def test_config():
    """Return a test configuration."""
    return {
        "conversation": {
            "max_history_per_conversation": 100,
            "persist_to_disk": False,
            "persist_path": "./conversations"
        }
    }

@pytest.fixture
def sample_messages():
    """Return sample conversation messages."""
    return [
        {"role": "user", "content": "Hello", "timestamp": "2023-01-01T00:00:00"},
        {"role": "assistant", "content": "Hi there!", "timestamp": "2023-01-01T00:00:01"},
        {"role": "user", "content": "How are you?", "timestamp": "2023-01-01T00:00:02"},
    ]

def test_conversation_manager_initialization(test_config):
    """Test ConversationManager initialization."""
    manager = ConversationManager(config=test_config)
    
    assert manager is not None
    assert manager.max_history == test_config["conversation"]["max_history_per_conversation"]
    assert isinstance(manager.conversations, dict)
    assert len(manager.conversations) == 0

def test_add_message_new_conversation(test_config):
    """Test adding a message to a new conversation."""
    manager = ConversationManager(config=test_config)
    
    # Add message to new conversation
    user_id = "test_user"
    conversation_id = "conv_123"
    message = {"role": "user", "content": "Hello", "timestamp": "2023-01-01T00:00:00"}
    
    manager.add_message(user_id, conversation_id, message)
    
    # Verify conversation was created
    assert conversation_id in manager.conversations[user_id]
    assert len(manager.conversations[user_id][conversation_id]) == 1
    assert manager.conversations[user_id][conversation_id][0] == message

def test_add_message_existing_conversation(test_config, sample_messages):
    """Test adding messages to an existing conversation."""
    manager = ConversationManager(config=test_config)
    user_id = "test_user"
    conversation_id = "conv_123"
    
    # Add initial messages
    for msg in sample_messages:
        manager.add_message(user_id, conversation_id, msg)
    
    # Verify messages were added
    assert len(manager.conversations[user_id][conversation_id]) == len(sample_messages)
    
    # Add another message
    new_message = {"role": "assistant", "content": "I'm doing well, thanks!", "timestamp": "2023-01-01T00:00:03"}
    manager.add_message(user_id, conversation_id, new_message)
    
    # Verify new message was added
    assert len(manager.conversations[user_id][conversation_id]) == len(sample_messages) + 1
    assert manager.conversations[user_id][conversation_id][-1] == new_message

def test_get_conversation_history(test_config, sample_messages):
    """Test retrieving conversation history."""
    manager = ConversationManager(config=test_config)
    user_id = "test_user"
    conversation_id = "conv_123"
    
    # Add sample messages
    for msg in sample_messages:
        manager.add_message(user_id, conversation_id, msg)
    
    # Get conversation history
    history = manager.get_conversation_history(user_id, conversation_id)
    
    # Verify history matches
    assert len(history) == len(sample_messages)
    assert history == sample_messages

def test_get_conversation_history_nonexistent(test_config):
    """Test getting history for a non-existent conversation."""
    manager = ConversationManager(config=test_config)
    
    # Try to get non-existent conversation
    history = manager.get_conversation_history("nonexistent_user", "nonexistent_conv")
    
    # Should return empty list
    assert history == []

def test_clear_conversation(test_config, sample_messages):
    """Test clearing a conversation."""
    manager = ConversationManager(config=test_config)
    user_id = "test_user"
    conversation_id = "conv_123"
    
    # Add sample messages
    for msg in sample_messages:
        manager.add_message(user_id, conversation_id, msg)
    
    # Clear conversation
    manager.clear_conversation(user_id, conversation_id)
    
    # Verify conversation is empty but still exists
    assert conversation_id in manager.conversations[user_id]
    assert len(manager.conversations[user_id][conversation_id]) == 0

def test_delete_conversation(test_config, sample_messages):
    """Test deleting a conversation."""
    manager = ConversationManager(config=test_config)
    user_id = "test_user"
    conversation_id = "conv_123"
    
    # Add sample messages
    for msg in sample_messages:
        manager.add_message(user_id, conversation_id, msg)
    
    # Delete conversation
    manager.delete_conversation(user_id, conversation_id)
    
    # Verify conversation was deleted
    assert user_id in manager.conversations
    assert conversation_id not in manager.conversations[user_id]

def test_list_conversations(test_config, sample_messages):
    """Test listing conversations for a user."""
    manager = ConversationManager(config=test_config)
    user_id = "test_user"
    
    # Create multiple conversations
    for i in range(3):
        conv_id = f"conv_{i}"
        manager.add_message(user_id, conv_id, {"role": "user", "content": f"Message {i}", "timestamp": f"2023-01-01T00:00:0{i}"})
    
    # List conversations
    conversations = manager.list_conversations(user_id)
    
    # Verify conversations are listed
    assert len(conversations) == 3
    assert all(conv_id in [f"conv_{i}" for i in range(3)] for conv_id in conversations)

def test_message_trimming(test_config):
    """Test that message history is trimmed to max length."""
    # Set max history to 2
    config = test_config.copy()
    config["conversation"]["max_history_per_conversation"] = 2
    
    manager = ConversationManager(config=config)
    user_id = "test_user"
    conversation_id = "conv_123"
    
    # Add more messages than max history
    for i in range(5):
        manager.add_message(user_id, conversation_id, {
            "role": "user",
            "content": f"Message {i}",
            "timestamp": f"2023-01-01T00:00:0{i}"
        })
    
    # Verify only the last 2 messages are kept
    history = manager.get_conversation_history(user_id, conversation_id)
    assert len(history) == 2
    assert "Message 3" in history[0]["content"]
    assert "Message 4" in history[1]["content"]

@patch('os.makedirs')
@patch('json.dump')
def test_save_conversations(mock_json_dump, mock_makedirs, test_config, tmp_path):
    """Test saving conversations to disk."""
    # Configure to persist to disk
    config = test_config.copy()
    config["conversation"]["persist_to_disk"] = True
    config["conversation"]["persist_path"] = str(tmp_path)
    
    manager = ConversationManager(config=config)
    user_id = "test_user"
    conversation_id = "conv_123"
    
    # Add a message
    manager.add_message(user_id, conversation_id, {
        "role": "user",
        "content": "Test message",
        "timestamp": "2023-01-01T00:00:00"
    })
    
    # Save conversations
    manager.save_conversations()
    
    # Verify save was attempted
    mock_makedirs.assert_called_once_with(str(tmp_path), exist_ok=True)
    assert mock_json_dump.called

@patch('os.path.exists', return_value=True)
@patch('json.load')
def test_load_conversations(mock_json_load, mock_exists, test_config, tmp_path):
    """Test loading conversations from disk."""
    # Configure to persist to disk
    config = test_config.copy()
    config["conversation"]["persist_to_disk"] = True
    config["conversation"]["persist_path"] = str(tmp_path)
    
    # Mock loaded data
    mock_data = {
        "test_user": {
            "conv_123": [
                {"role": "user", "content": "Test message", "timestamp": "2023-01-01T00:00:00"}
            ]
        }
    }
    mock_json_load.return_value = mock_data
    
    manager = ConversationManager(config=config)
    
    # Load conversations
    manager.load_conversations()
    
    # Verify conversations were loaded
    assert "test_user" in manager.conversations
    assert "conv_123" in manager.conversations["test_user"]
    assert len(manager.conversations["test_user"]["conv_123"]) == 1
    assert manager.conversations["test_user"]["conv_123"][0]["content"] == "Test message"
