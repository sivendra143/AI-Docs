# app.py

import os
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from document_processor import DocumentProcessor
from llm_rag import ChatbotLLM
from api import setup_api_routes
from voice_input import setup_voice_routes
from websocket import setup_websocket

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*", "file:///*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Global variables
config = None
processor = None
chatbot = None
vector_store = None

def initialize_app(config_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')):
    global config, processor, chatbot, vector_store
    
    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Ensure docs folder exists
    docs_folder = config['docs_folder']
    if not os.path.exists(docs_folder):
        os.makedirs(docs_folder)
        print(f"Created documents folder: {docs_folder}")
    
    # Process documents if any exist
    processor = DocumentProcessor(docs_folder, config_path)
    processor.process_documents()
    vector_store = processor.get_vector_store()
    
    if vector_store:
        # Initialize chatbot
        chatbot = ChatbotLLM(vector_store, config_path)
        print("Chatbot initialized successfully!")
    else:
        print("No document content was processed. Please add documents to the folder.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/api/refresh', methods=['POST'])
def refresh():
    global processor, vector_store, chatbot
    
    # Re-process documents
    processor.process_documents()
    vector_store = processor.get_vector_store()
    
    if vector_store:
        chatbot = ChatbotLLM(vector_store, 'config.json')
        return jsonify({'status': 'success', 'message': 'Documents refreshed successfully.'})
    else:
        return jsonify({'status': 'error', 'message': 'No documents found to process.'})

if __name__ == '__main__':
    initialize_app()
    
    # Setup API routes
    setup_api_routes(app, chatbot)
    
    # Setup voice routes
    setup_voice_routes(app, chatbot)
    
    # Setup WebSocket
    socketio = setup_websocket(app, chatbot)
    
    # Run the app with socketio
    socketio.run(app, host=config['host'], port=config['port'], debug=True)

