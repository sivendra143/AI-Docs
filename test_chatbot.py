"""
Test script for the ChatbotLLM class.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from pprint import pprint

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_chatbot(question, config_path=None, vector_store_path=None):
    """Test the chatbot with a question."""
    print("\n" + "="*50)
    print("🤖 Testing Chatbot")
    print("="*50 + "\n")
    
    try:
        from src.llm_rag import ChatbotLLM
        from langchain.vectorstores import FAISS
        from sentence_transformers import SentenceTransformer
        
        print(f"❓ Question: {question}")
        
        # Load or create vector store
        if vector_store_path and os.path.exists(vector_store_path):
            print(f"\n📂 Loading vector store from: {vector_store_path}")
            embeddings = SentenceTransformer('all-MiniLM-L6-v2')
            vector_store = FAISS.load_local(vector_store_path, embeddings)
        else:
            print("\n⚠️ No vector store found. The chatbot will not have document context.")
            vector_store = None
        
        # Initialize the chatbot
        print("\n🤖 Initializing chatbot...")
        chatbot = ChatbotLLM(
            vector_store=vector_store,
            config_path=config_path
        )
        
        # Ask the question
        print(f"\n💬 Sending question to chatbot...")
        response = chatbot.ask_question(question)
        
        if not response:
            print("\n❌ Failed to get response from chatbot")
            return False
        
        # Print the response
        print("\n✅ Response received:")
        print(f"   💬 Answer: {response.get('answer', 'No answer provided')}")
        
        if "sources" in response and response["sources"]:
            print("\n📚 Sources:")
            for i, source in enumerate(response["sources"], 1):
                print(f"   {i}. {source.get('title', 'Untitled')} (page {source.get('page', 'N/A')})")
        
        if "suggested_questions" in response and response["suggested_questions"]:
            print("\n❓ Suggested follow-up questions:")
            for i, q in enumerate(response["suggested_questions"], 1):
                print(f"   {i}. {q}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing chatbot: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Test Chatbot')
    parser.add_argument('question', type=str, nargs='?', 
                       default='What is this document about?',
                       help='Question to ask (default: "What is this document about?"')
    parser.add_argument('--config', type=str, default='config.json',
                       help='Path to config file (default: config.json)')
    parser.add_argument('--vector-store', type=str, default='vector_store',
                       help='Path to vector store directory (default: vector_store)')
    
    args = parser.parse_args()
    
    # Convert to absolute paths
    config_path = os.path.abspath(args.config) if os.path.exists(args.config) else None
    vector_store_path = os.path.abspath(args.vector_store) if os.path.exists(args.vector_store) else None
    
    print(f"⚙️  Config file: {config_path if config_path else 'Using defaults'}")
    print(f"📚 Vector store: {vector_store_path if vector_store_path else 'Not found'}")
    
    # Run the test
    success = test_chatbot(args.question, config_path, vector_store_path)
    
    if success:
        print("\n✅ Chatbot test completed successfully!")
    else:
        print("\n❌ Chatbot test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
