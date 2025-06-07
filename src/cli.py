# cli.py

import os
import argparse
import json
from document_processor import DocumentProcessor
from llm_rag import ChatbotLLM

def load_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description='PDF Chatbot CLI')
    parser.add_argument('--config', type=str, default='config.json', help='Path to config file')
    parser.add_argument('--docs_folder', type=str, help='Path to documents folder (overrides config)')
    args = parser.parse_args()

    # Load configuration
    config_path = args.config
    config = load_config(config_path)

    # Override config with command line arguments if provided
    if args.docs_folder:
        config['docs_folder'] = args.docs_folder

    # Ensure documents folder exists
    docs_folder = config['docs_folder']
    if not os.path.exists(docs_folder):
        os.makedirs(docs_folder)
        print(f"Created documents folder: {docs_folder}")
        print(f"Please add documents to {docs_folder} and restart the application.")
        return

    # Process documents
    print(f"Processing documents from {docs_folder}...")
    processor = DocumentProcessor(docs_folder)
    processor.process_documents()
    vector_store = processor.get_vector_store()

    if not vector_store:
        print("No document content was processed. Please add documents to the folder and try again.")
        return

    # Initialize chatbot
    print("Initializing chatbot...")
    chatbot = ChatbotLLM(vector_store, config_path)

    # Interactive chat loop
    print("\nPDF Chatbot is ready! Type 'exit' to quit.")
    print("="*50)
    
    while True:
        question = input("\nYou: ")
        if question.lower() in ['exit', 'quit', 'q']:
            break
        
        answer = chatbot.ask_question(question)
        print(f"\nChatbot: {answer}")
        
        # Show suggestions
        suggestions = chatbot.get_smart_suggestions(question, answer)
        print("\nSuggested follow-up questions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")

if __name__ == "__main__":
    main()

