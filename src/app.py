# src/app.py

import os
import sys
import json
from flask import Flask, jsonify, render_template, redirect, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash
from flask_cors import CORS

# Add parent directory to path for local execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the package
from . import create_app, db
from . import socketio  # Import the shared socketio instance
from .models import User, Conversation, Message
from .websocket import setup_websocket

# Globals
processor = None
chatbot = None
vector_store = None
conversation_manager = None


def initialize_components(app, config_path=None):
    global processor, vector_store, conversation_manager, chatbot

    # Load config if provided
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            app.config.update(json.load(f))
    
    # Set default config values if not provided
    app.config.setdefault('UPLOAD_FOLDER', 'uploads')
    app.config.setdefault('DOCS_FOLDER', 'docs')
    app.config.setdefault('VECTOR_STORE_PATH', 'vector_store')
    app.config.setdefault('MAX_CONVERSATION_HISTORY', 10)  # Number of messages to keep in memory
    
    # Create necessary directories
    for folder in [app.config['UPLOAD_FOLDER'], app.config['DOCS_FOLDER']]:
        os.makedirs(folder, exist_ok=True)
    
    # Initialize app.extensions if it doesn't exist
    if not hasattr(app, 'extensions'):
        app.extensions = {}
    
    try:
        from src.document_processor import DocumentProcessor
        from src.llm_rag import ChatbotLLM
        from src.conversation_manager import ConversationManager
        
        print("\n" + "="*50)
        print(">> Initializing AI Document Chat Application")
        print("="*50 + "\n")
        
        # Initialize conversation manager first
        print("💬 Initializing conversation manager...")
        conversation_manager = ConversationManager(
            max_history_per_conversation=app.config['MAX_CONVERSATION_HISTORY']
        )
        app.extensions['conversation_manager'] = conversation_manager
        print("✅ Conversation manager ready")
        
        # Initialize document processor
        print("\n📂 Initializing document processor...")
        processor = DocumentProcessor(
            docs_folder=app.config['DOCS_FOLDER'],
            config_path=config_path if config_path else 'config.json'
        )
        
        # Process documents and get vector store
        print("📄 Processing documents...")
        if not processor.process_documents():
            print("⚠️ No documents processed. Place documents in the 'docs' folder.")
            # Continue with empty vector store
            processor.vector_store = None
        
        # Initialize chatbot with the processed vector store
        print("\n🤖 Initializing chatbot...")
        chatbot = ChatbotLLM(
            vector_store=processor.vector_store if hasattr(processor, 'vector_store') and processor.vector_store else None,
            config_path=config_path if config_path else 'config.json'
        )
        
        # Store components in app context for WebSocket access
        app.extensions.update({
            'processor': processor,
            'chatbot': chatbot,
            'vector_store': getattr(processor, 'vector_store', None),
            'conversation_manager': conversation_manager
        })
        
        # Set global variables
        vector_store = getattr(processor, 'vector_store', None)
        
        print("\n" + "="*50)
        print("✅ Application components initialized successfully")
        print("="*50 + "\n")
        
        # Print status
        print(f"📊 Status:")
        print(f"   - Documents processed: {len(processor.vector_store.docstore._dict) if processor.vector_store else 0}")
        print(f"   - Conversation history: {len(conversation_manager.get_active_conversations())} active conversations")
        print("\n>> Application is ready to accept connections!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing components: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def setup_app():
    # Ensure required directories exist
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for directory in ['instance', 'uploads', 'static']:
        os.makedirs(os.path.join(base_dir, directory), exist_ok=True)
    
    # Create the Flask app
    app = create_app('development')
    
    # Initialize application components
    if not initialize_components(app):
        print("❌ Failed to initialize application components")
        return None, app
    
    # Import blueprints
    from .routes import api_bp, root_bp
    
    # Clear any existing blueprints to avoid conflicts
    if hasattr(app, 'blueprints'):
        app.blueprints.clear()
    
    # Register the API blueprint with /api prefix if not already registered
    if 'api' not in app.blueprints:
        app.register_blueprint(api_bp, name='api', url_prefix='/api')
    
    # Register the root blueprint with no prefix if not already registered
    if 'root_blueprint' not in app.blueprints:
        app.register_blueprint(root_bp, name='root_blueprint')
    
    # Error handlers are registered in __init__.py
    
    try:
        from flask_swagger_ui import get_swaggerui_blueprint
        swaggerui_blueprint = get_swaggerui_blueprint(
            '/docs', '/static/swagger.json', config={'app_name': "Flask AI App"}
        )
        app.register_blueprint(swaggerui_blueprint, url_prefix='/docs')
    except ImportError:
        print("⚠️ Flask-Swagger-UI not installed. API documentation will not be available.")
    
    # Ensure instance directory exists
    instance_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Database initialization is now handled in __init__.py
    print("✅ Application setup complete")
    
    # Create test user in development mode
    if app.debug:
        with app.app_context():
            test_user = User.query.filter_by(username='test').first()
            if not test_user:
                test_user = User(
                    username='test',
                    email='test@example.com',
                    password=generate_password_hash('test123'),
                    is_admin=False,
                    preferred_language='en'
                )
                db.session.add(test_user)
                print("👤 Created test user")
                db.session.commit()

    # Initialize WebSocket setup with the chatbot instance
    try:
        from src.websocket import setup_websocket
        # Get chatbot from app.extensions where it was stored during component initialization
        chatbot = app.extensions.get('chatbot')
        if chatbot is None:
            print("⚠️ Chatbot not found in app.extensions")
        socketio = setup_websocket(app, chatbot)
    except ImportError as e:
        print(f"⚠️ WebSocket setup failed: {str(e)}")
        socketio = None
    except Exception as e:
        print(f"⚠️ Error setting up WebSocket: {str(e)}")
        import traceback


def create_application():
    """Create and configure the Flask application."""
    app = create_app()
    
    # Initialize WebSocket
    setup_websocket(app)
    
    # Initialize components
    initialize_components(app)
    
    return app

if __name__ == '__main__':
    # Create application
    app = create_application()
    
    # Get the socketio instance from app extensions
    socketio = app.extensions.get('socketio')
    
    if not socketio:
        raise RuntimeError("Socket.IO not properly initialized")
    
    # Run the application
    try:
        print(">> Starting WebSocket server...")
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=True, 
            use_reloader=True, 
            allow_unsafe_werkzeug=True,
            log_output=True
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        raise
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)
