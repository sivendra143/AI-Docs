"""
Tests for the DocumentProcessor class.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.document_processor import DocumentProcessor

def test_document_processor_initialization(test_config_file, test_docs_dir):
    """Test DocumentProcessor initialization."""
    processor = DocumentProcessor(config_path=test_config_file)
    
    assert processor is not None
    assert processor.docs_folder == test_docs_dir
    assert processor.chunk_size == 1000
    assert processor.chunk_overlap == 200

@pytest.mark.asyncio
async def test_load_documents(test_config_file, test_docs_dir):
    """Test loading documents from the test directory."""
    processor = DocumentProcessor(config_path=test_config_file)
    
    # Test loading documents
    documents = await processor.load_documents()
    
    assert len(documents) > 0
    assert "test document" in documents[0].page_content.lower()

def test_split_documents(test_config_file):
    """Test document splitting functionality."""
    from langchain.schema import Document
    
    processor = DocumentProcessor(config_path=test_config_file)
    
    # Create test documents
    test_docs = [
        Document(
            page_content="This is a test document. " * 50,  # ~1000 chars
            metadata={"source": "test.txt", "page": 1}
        )
    ]
    
    # Split documents
    splits = processor.split_documents(test_docs)
    
    assert len(splits) > 1  # Should be split into multiple chunks
    assert len(splits[0].page_content) <= 1000  # Should respect chunk size

@pytest.mark.asyncio
async def test_process_documents(test_config_file, test_docs_dir):
    """Test the complete document processing pipeline."""
    with patch('src.document_processor.OpenAIEmbeddings') as mock_embeddings, \
         patch('src.document_processor.FAISS') as mock_faiss:
        
        # Setup mock embeddings
        mock_embeddings.return_value.embed_documents.return_value = [[0.1] * 384] * 5
        
        # Setup mock FAISS
        mock_index = MagicMock()
        mock_faiss.from_documents.return_value = mock_index
        
        # Initialize processor
        processor = DocumentProcessor(config_path=test_config_file)
        
        # Process documents
        vector_store = await processor.process_documents()
        
        # Verify results
        assert vector_store is not None
        mock_faiss.from_documents.assert_called_once()
        
        # Verify save was called if persist is True
        if processor.persist_directory:
            mock_index.save_local.assert_called_once_with(
                folder_path=processor.persist_directory,
                index_name=processor.index_name
            )

def test_supported_file_types():
    """Test that supported file types are correctly identified."""
    from src.document_processor import DocumentProcessor
    
    processor = DocumentProcessor()
    
    # Test supported file types
    assert processor.is_supported_file("document.pdf") is True
    assert processor.is_supported_file("document.docx") is True
    assert processor.is_supported_file("document.txt") is True
    
    # Test unsupported file types
    assert processor.is_supported_file("document.xyz") is False
    assert processor.is_supported_file("document") is False

@pytest.mark.asyncio
async def test_load_nonexistent_directory(test_config_file):
    """Test loading from a non-existent directory."""
    processor = DocumentProcessor(config_path=test_config_file)
    processor.docs_folder = "/nonexistent/directory"
    
    with pytest.raises(FileNotFoundError):
        await processor.load_documents()

@pytest.mark.asyncio
async def test_empty_directory(test_config_file, tmp_path):
    """Test processing an empty directory."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    
    processor = DocumentProcessor(config_path=test_config_file)
    processor.docs_folder = str(empty_dir)
    
    with pytest.raises(ValueError, match="No supported documents found"):
        await processor.process_documents()

def test_chunk_size_validation():
    """Test validation of chunk size and overlap."""
    from src.document_processor import DocumentProcessor
    
    # Test valid chunk size and overlap
    processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
    assert processor.chunk_size == 1000
    assert processor.chunk_overlap == 200
    
    # Test invalid chunk size
    with pytest.raises(ValueError):
        DocumentProcessor(chunk_size=0)
    
    # Test invalid chunk overlap (negative)
    with pytest.raises(ValueError):
        DocumentProcessor(chunk_overlap=-100)
    
    # Test chunk overlap larger than chunk size
    with pytest.raises(ValueError):
        DocumentProcessor(chunk_size=500, chunk_overlap=600)
