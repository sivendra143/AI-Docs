"""
The application factory module.

This module contains the application factory function.
"""
import os
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

# Import extensions from extensions module to avoid circular imports
from .extensions import db, login_manager, socketio, cors
from .websocket import setup_websocket

# Export socketio for use in other modules
__all__ = ['db', 'login_manager', 'socketio', 'cors', 'create_app', 'setup_websocket']

# Set login manager settings
login_manager.login_view = 'api_blueprint.login'  # Changed from 'api_bp.login_redirect' to 'api_blueprint.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

def create_app(config_name=None):
    """Create and configure the Flask application.
    
    Args:
        config_name (str, optional): The configuration to use. Defaults to the value of the 
            FLASK_ENV environment variable, or 'development' if not set.
            
    Returns:
        Flask: The configured Flask application instance.
    """
    from .config import config
    
    # Create the Flask application
    app = Flask(__name__, 
               static_folder='static', 
               static_url_path='',
               template_folder='templates')
    
    # Configure the application
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Set BASE_DIR in config before loading other configs
    app.config['BASE_DIR'] = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Import routes after extensions are initialized to avoid circular imports
    from .routes import api_bp, root_bp
    
    # Clear any existing blueprints to avoid conflicts
    if hasattr(app, 'blueprints'):
        app.blueprints.clear()
    
    # Register blueprints with unique names if not already registered
    if 'api_blueprint' not in app.blueprints:
        app.register_blueprint(api_bp, name='api_blueprint', url_prefix='/api')
    
    if 'root_blueprint' not in app.blueprints:
        app.register_blueprint(root_bp, name='root_blueprint')
        
    # Register AJAX fallback routes for when WebSocket is unavailable
    from .routes_ajax import ajax_bp
    if 'ajax_blueprint' not in app.blueprints:
        app.register_blueprint(ajax_bp, name='ajax_blueprint')
    
    # Import the Socket.IO instance
    from . import socketio as app_socketio
    
    # Configure CORS for the application
    app.config['CORS_HEADERS'] = 'Content-Type,Authorization'
    app.config['CORS_ORIGINS'] = '*'  # Allow all origins in development
    
    # Initialize CORS with the app
    cors.init_app(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True,
            "expose_headers": ["Content-Type", "Authorization"],
            "max_age": 600
        }
    })
    
    # Initialize app.extensions if it doesn't exist
    if not hasattr(app, 'extensions'):
        app.extensions = {}
    
    # Initialize Socket.IO with the app
    if 'socketio' not in app.extensions:
        try:
            # Initialize Socket.IO with the app
            app_socketio.init_app(app)
            print("✅ Socket.IO initialized with app")
            
            # Store socketio in app extensions
            app.extensions['socketio'] = app_socketio
        except Exception as e:
            print(f"❌ Error initializing Socket.IO: {str(e)}")
            raise
    else:
        print("ℹ️  Socket.IO already initialized, skipping...")
        app_socketio = app.extensions['socketio']
    
    # Log Socket.IO configuration
    if app.debug:
        print("\n🔌 Socket.IO Configuration:")
        print(f"   - CORS Allowed Origins: *")
        print(f"   - Async Mode: {app_socketio.async_mode}")
        print(f"   - Path: {app_socketio.server_options.get('path', '/socket.io')}")
        print(f"   - Transports: {app_socketio.server_options.get('transports', ['websocket', 'polling'])}")
        print(f"   - Debug: {app.debug}")
        print(f"   - Testing: {app.testing}\n")
    
    # CORS is already configured above, no need to configure it again
    
    # Initialize database within app context
    with app.app_context():
        try:
            # Import models after db is initialized to ensure they're registered with SQLAlchemy
            from .models import User
            from werkzeug.security import generate_password_hash
            
            print("🔨 Creating database tables...")
            # Create all database tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Database tables: {tables}")
            
            # Store socketio in app.extensions for access in other modules
            if not hasattr(app, 'extensions'):
                app.extensions = {}
                
            # Initialize WebSocket
            print("🔌 Initializing WebSocket...")
            from .llm_rag import ChatbotLLM
            from .vector_store import get_vector_store
            
            try:
                # Initialize vector store and chatbot
                print("🔍 Initializing vector store...")
                vector_store = get_vector_store()
                print("🤖 Initializing ChatbotLLM...")
                chatbot = ChatbotLLM(vector_store)
                
                # Store chatbot in app.extensions
                app.extensions['chatbot'] = chatbot
                print("✅ Chatbot initialized successfully")
                
                # Setup WebSocket with the app and chatbot
                print("🔌 Setting up WebSocket...")
                socketio = setup_websocket(app, chatbot)
                app.extensions['socketio'] = socketio
                print("✅ WebSocket initialized successfully")
                
            except Exception as e:
                print(f"❌ Error initializing WebSocket or Chatbot: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
            
            # Create admin user if it doesn't exist
            print("👤 Checking admin user...")
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password=generate_password_hash('admin123'),
                    is_admin=True,
                    preferred_language='en'
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Created admin user (admin/admin123)")
            else:
                print("✅ Admin user already exists")
            
        except Exception as e:
            print(f"❌ Error initializing database: {str(e)}")
            import traceback
            traceback.print_exc()
            exit(1)
    
    # CORS is already configured above, no need to configure it again
    
    # Socket.IO is already initialized above, no need to initialize again
    if 'root_blueprint' not in app.blueprints:
        app.register_blueprint(root_bp, name='root_blueprint')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Apply proxy fix if running behind a reverse proxy
    if app.config.get('BEHIND_PROXY', False):
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,
            x_proto=1,
            x_host=1,
            x_prefix=1
        )
    
    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Database is already initialized above, no need to initialize again
    
    return app


def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'status': 'error',
            'message': 'Bad request',
            'error': str(error)
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'status': 'error',
            'message': 'Unauthorized',
            'error': str(error)
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'status': 'error',
            'message': 'Forbidden',
            'error': str(error)
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'message': 'Resource not found',
            'error': str(error)
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'status': 'error',
            'message': 'Method not allowed',
            'error': str(error)
        }), 405
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error': str(error) if app.debug else 'An internal error occurred.'
        }), 500
