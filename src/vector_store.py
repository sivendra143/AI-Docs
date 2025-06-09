"""
Module for handling the vector store for document embeddings.
"""
import os
import json
import numpy as np
from typing import Optional, List
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

class DummyEmbeddings(Embeddings):
    """Dummy embeddings for testing without internet access."""
    
    def __init__(self, size: int = 384):
        self.size = size
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents using dummy embeddings."""
        return [list(np.random.rand(self.size).astype(np.float32)) for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a query using dummy embeddings."""
        return list(np.random.rand(self.size).astype(np.float32))

def get_vector_store():
    """
    Initialize and return a vector store with dummy embeddings.
    
    Returns:
        FAISS: An instance of FAISS vector store with dummy embeddings.
    """
    try:
        print("🔍 Initializing vector store with dummy embeddings...")
        
        # Load configuration
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Use dummy embeddings that don't require internet
        print("🔧 Using dummy embeddings (no internet required)")
        embeddings = DummyEmbeddings(size=384)  # 384 is the size of MiniLM-L6-v2 embeddings
        
        # Create or load FAISS index
        vector_store_path = config.get('VECTOR_STORE_PATH', 'vector_store')
        
        # Create directory if it doesn't exist
        os.makedirs(vector_store_path, exist_ok=True)
        
        # Check if the FAISS index files exist
        index_file = os.path.join(vector_store_path, 'index.faiss')
        if os.path.exists(index_file):
            print(f"📂 Loading existing vector store from {vector_store_path}")
            try:
                return FAISS.load_local(
                    vector_store_path, 
                    embeddings,
                    allow_dangerous_deserialization=True  # Safe since we trust our local files
                )
            except Exception as e:
                print(f"⚠️ Error loading existing vector store: {e}")
        else:
            print("🆕 Creating new vector store (no existing index found)")
        
        # Create an empty FAISS index with a dummy document
        return FAISS.from_texts(["Initial document"], embeddings)

    except Exception as e:
        print(f"❌ Error initializing vector store: {e}")
        raise

def save_vector_store(vector_store, path: str = None):
    """
    Save the vector store to disk.
    
    Args:
        vector_store: The FAISS vector store to save.
        path (str, optional): The path to save the vector store to. 
                            Defaults to the path specified in the config.
    """
    if path is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        path = config.get('VECTOR_STORE_PATH', 'vector_store')
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Save the vector store
    vector_store.save_local(path)
    print(f"💾 Vector store saved to {path}")
