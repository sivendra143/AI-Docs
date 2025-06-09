"""
Tests for the ChatbotLLM class.
"""
import os
import sys
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chatbot import ChatbotLLM

@pytest.fixture
def test_config():
    """Return a test configuration."""
    return {
        "llm": {
            "model_name": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000,
            "api_key": "test-api-key",
            "api_base": "http://test-api"
        },
        "embedding": {
            "model_name": "all-MiniLM-L6-v2"
        },
        "prompt_templates": {
            "qa": "Test QA template: {question}\nContext: {context}",
            "chat": "Test Chat template: {input}"
        }
    }

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    mock = MagicMock()
    mock.similarity_search.return_value = [
        {"page_content": "Test document content", "metadata": {"source": "test.pdf", "page": 1}}
    ]
    return mock

@pytest.mark.asyncio
async def test_chatbot_initialization(test_config, mock_vector_store):
    """Test ChatbotLLM initialization."""
    with patch('src.chatbot.ChatOpenAI') as mock_chat:
        mock_chat.return_value = AsyncMock()
        
        chatbot = ChatbotLLM(
            vector_store=mock_vector_store,
            config=test_config
        )
        
        assert chatbot is not None
        assert chatbot.vector_store == mock_vector_store
        assert chatbot.model_name == test_config["llm"]["model_name"]
        assert chatbot.temperature == test_config["llm"]["temperature"]
        assert chatbot.max_tokens == test_config["llm"]["max_tokens"]

@pytest.mark.asyncio
async def test_generate_response(test_config, mock_vector_store):
    """Test generating a response from the chatbot."""
    with patch('src.chatbot.ChatOpenAI') as mock_chat:
        # Setup mock LLM
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="Test response")
        mock_chat.return_value = mock_llm
        
        # Initialize chatbot
        chatbot = ChatbotLLM(
            vector_store=mock_vector_store,
            config=test_config
        )
        
        # Test generate response
        question = "What is the test about?"
        response = await chatbot.generate_response(question)
        
        # Verify response
        assert response == "Test response"
        
        # Verify vector store was queried
        mock_vector_store.similarity_search.assert_called_once_with(question, k=4)
        
        # Verify LLM was called with the right arguments
        mock_llm.ainvoke.assert_awaited_once()

@pytest.mark.asyncio
async def test_chat_with_history(test_config, mock_vector_store):
    """Test chat with conversation history."""
    with patch('src.chatbot.ChatOpenAI') as mock_chat:
        # Setup mock LLM
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="Test response with history")
        mock_chat.return_value = mock_llm
        
        # Initialize chatbot
        chatbot = ChatbotLLM(
            vector_store=mock_vector_store,
            config=test_config
        )
        
        # Test chat with history
        conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        response = await chatbot.chat("How are you?", conversation)
        
        # Verify response
        assert response == "Test response with history"
        
        # Verify LLM was called with the conversation history
        args, _ = mock_llm.ainvoke.call_args
        assert any("Hello" in str(arg) for arg in args)
        assert any("Hi there!" in str(arg) for arg in args)

@pytest.mark.asyncio
async def test_ask_question(test_config, mock_vector_store):
    """Test asking a question with sources."""
    with patch('src.chatbot.ChatOpenAI') as mock_chat:
        # Setup mock LLM
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(
            content=json.dumps({
                "answer": "Test answer",
                "sources": ["test.pdf"]
            })
        )
        mock_chat.return_value = mock_llm
        
        # Initialize chatbot
        chatbot = ChatbotLLM(
            vector_store=mock_vector_store,
            config=test_config
        )
        
        # Test ask question
        question = "What is the test about?"
        result = await chatbot.ask(question)
        
        # Verify result
        assert isinstance(result, dict)
        assert "answer" in result
        assert "sources" in result
        assert result["answer"] == "Test answer"
        assert "test.pdf" in result["sources"][0]

@pytest.mark.asyncio
async def test_stream_response(test_config, mock_vector_store):
    """Test streaming response from the chatbot."""
    with patch('src.chatbot.ChatOpenAI') as mock_chat:
        # Setup mock LLM with streaming
        mock_llm = AsyncMock()
        mock_chat.return_value = mock_llm
        
        # Create mock async generator for streaming
        async def mock_astream(*args, **kwargs):
            for chunk in ["Test", " response", " stream"]:
                yield MagicMock(content=chunk)
        
        mock_llm.astream = mock_astream
        
        # Initialize chatbot
        chatbot = ChatbotLLM(
            vector_store=mock_vector_store,
            config=test_config
        )
        
        # Test streaming response
        question = "Stream a response"
        chunks = []
        
        async for chunk in chatbot.stream_response(question):
            chunks.append(chunk)
        
        # Verify chunks were streamed correctly
        assert len(chunks) == 3
        assert "".join(chunks) == "Test response stream"

@pytest.mark.asyncio
async def test_error_handling(test_config, mock_vector_store):
    """Test error handling in the chatbot."""
    with patch('src.chatbot.ChatOpenAI') as mock_chat:
        # Setup mock LLM that raises an exception
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("Test error")
        mock_chat.return_value = mock_llm
        
        # Initialize chatbot
        chatbot = ChatbotLLM(
            vector_store=mock_vector_store,
            config=test_config
        )
        
        # Test error handling
        with pytest.raises(Exception) as exc_info:
            await chatbot.generate_response("Test question")
        
        assert "Test error" in str(exc_info.value)

def test_prepare_prompt(test_config, mock_vector_store):
    """Test prompt preparation."""
    with patch('src.chatbot.ChatOpenAI'):
        # Initialize chatbot
        chatbot = ChatbotLLM(
            vector_store=mock_vector_store,
            config=test_config
        )
        
        # Test QA prompt
        qa_prompt = chatbot._prepare_prompt(
            "qa",
            question="Test question",
            context=["Context 1", "Context 2"]
        )
        assert "Test question" in qa_prompt
        assert "Context 1" in qa_prompt
        
        # Test chat prompt
        chat_prompt = chatbot._prepare_prompt(
            "chat",
            input="Test input"
        )
        assert "Test input" in chat_prompt

@pytest.mark.asyncio
async def test_get_similar_documents(test_config, mock_vector_store):
    """Test getting similar documents from the vector store."""
    with patch('src.chatbot.ChatOpenAI'):
        # Initialize chatbot
        chatbot = ChatbotLLM(
            vector_store=mock_vector_store,
            config=test_config
        )
        
        # Test getting similar documents
        question = "Test question"
        docs = await chatbot.get_similar_documents(question)
        
        # Verify vector store was queried
        mock_vector_store.similarity_search.assert_called_once_with(question, k=4)
        assert len(docs) > 0
