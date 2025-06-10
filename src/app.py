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

from src.extensions import db
from src import create_app
from src.models import User, Conversation, Message

# Globals
processor = None
vector_store = None
conversation_manager = None

# Import and initialize the Chatbot for WebSocket chat
from src.services.chat_service import Chatbot
chatbot = Chatbot()


def initialize_components(app, config_path=None):
    global processor, chatbot, vector_store, conversation_manager

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            app.config.update(json.load(f))

    uploads_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(uploads_folder, exist_ok=True)

    docs_folder = app.config.get('DOCS_FOLDER', 'docs')
    os.makedirs(docs_folder, exist_ok=True)

    try:
        from src.document_processor import DocumentProcessor
        from src.llm_rag import ChatbotLLM
        from src.conversation_manager import ConversationManager

        processor = DocumentProcessor(app.config)
        chatbot = ChatbotLLM(app.config)
        processor.process_documents()
        vector_store = processor.vector_store
        conversation_manager = ConversationManager()

        print("✅ Application components initialized")
        return True
    except Exception as e:
        print(f"❌ Error initializing components: {str(e)}")
        return False


def setup_app():
    # Ensure required directories exist
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for directory in ['instance', 'uploads', 'static']:
        os.makedirs(os.path.join(base_dir, directory), exist_ok=True)
    
    # Create the Flask app
    app = create_app()
    
    # Register Blueprints
    from src.routes import api_bp, root_bp
    from src.admin_routes import admin_bp
    
    # Only register the blueprints if they're not already registered
    if 'api' not in app.blueprints:
        app.register_blueprint(api_bp, url_prefix='/api')
    
    if 'root' not in app.blueprints:
        app.register_blueprint(root_bp, url_prefix='/')
        
    if 'admin' not in app.blueprints:
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Register voice input routes
    from src.voice_input import setup_voice_routes
    setup_voice_routes(app, chatbot)

    # Register Swagger (optional)
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

    # Initialize WebSocket setup
    try:
        from src.websocket import setup_websocket
        socketio = setup_websocket(app, chatbot)
    except ImportError as e:
        print(f"⚠️ WebSocket setup failed: {str(e)}")
        socketio = None

    return socketio, app


if __name__ == '__main__':
    socketio, app = setup_app()

    for rule in app.url_map.iter_rules():
        print(f"[ROUTE] {rule} -> {rule.endpoint}")

    if socketio:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)
