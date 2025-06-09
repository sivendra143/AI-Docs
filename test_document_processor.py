"""
Test script for the DocumentProcessor class.
"""
import os
import sys
import argparse
from pathlib import Path
from pprint import pprint

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_document_processing(docs_folder, config_path=None):
    """Test document processing with the given configuration."""
    print("\n" + "="*50)
    print("📄 Testing Document Processor")
    print("="*50 + "\n")
    
    try:
        from src.document_processor import DocumentProcessor
        
        print(f"📂 Loading documents from: {docs_folder}")
        
        # Initialize the document processor
        processor = DocumentProcessor(
            docs_folder=docs_folder,
            config_path=config_path
        )
        
        # Process documents
        print("\n🔄 Processing documents...")
        success = processor.process_documents()
        
        if not success:
            print("\n❌ Failed to process documents")
            return False
        
        # Get the vector store
        vector_store = processor.get_vector_store()
        
        if vector_store is None:
            print("\n❌ Failed to create vector store")
            return False
        
        # Print document statistics
        docstore = vector_store.docstore._dict
        print(f"\n✅ Successfully processed {len(docstore)} document chunks")
        
        # Print sample document chunks
        print("\n📝 Sample document chunks:")
        for i, (doc_id, doc) in enumerate(list(docstore.items())[:3], 1):
            print(f"\n--- Chunk {i} ---")
            print(f"ID: {doc_id}")
            print(f"Content: {doc.page_content[:200]}...")
            if hasattr(doc, 'metadata'):
                print(f"Metadata: {doc.metadata}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing document processor: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Test Document Processor')
    parser.add_argument('--docs-folder', type=str, default='docs',
                       help='Path to the documents folder (default: docs)')
    parser.add_argument('--config', type=str, default='config.json',
                       help='Path to config file (default: config.json)')
    
    args = parser.parse_args()
    
    # Convert to absolute path
    docs_folder = os.path.abspath(args.docs_folder)
    config_path = os.path.abspath(args.config) if os.path.exists(args.config) else None
    
    print(f"📁 Documents folder: {docs_folder}")
    print(f"⚙️  Config file: {config_path if config_path else 'Using defaults'}")
    
    # Run the test
    success = test_document_processing(docs_folder, config_path)
    
    if success:
        print("\n✅ Document processor test completed successfully!")
    else:
        print("\n❌ Document processor test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
