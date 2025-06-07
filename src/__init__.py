"""
The application factory module.

This module contains the application factory function.
"""
import os
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

# Import extensions from extensions module to avoid circular imports
from .extensions import db, login_manager, socketio, cors

# Set login manager settings
login_manager.login_view = 'api_bp.login_redirect'
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
    
    # Register blueprints with unique names
    app.register_blueprint(api_bp, name='api_blueprint', url_prefix='/api')
    app.register_blueprint(root_bp, name='root_blueprint')
    
    # Configure CORS
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', '*'),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        },
        r"/static/*": {
            "origins": "*"
        }
    })
    
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
    
    # Configure CORS
    cors.init_app(app, resources={
        r"/*": {
            "origins": "*",
            "supports_credentials": True,
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })
    
    # Initialize Socket.IO with CORS support
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=app.debug,
        cors_credentials=True
    )
    
    # Import blueprints
    from .routes import api_bp, root_bp
    
    # Register the API blueprint with /api prefix
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register the root blueprint with no prefix
    app.register_blueprint(root_bp, url_prefix='/')
    
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
    
    # Initialize database
    with app.app_context():
        from . import database
        if not database.init_database():
            print("❌ Failed to initialize database")
            exit(1)
        print("✅ Database initialized successfully")
        
        # Create admin user if it doesn't exist
        if database.create_admin_user():
            print("👤 Created default admin user (admin/admin123)")
        else:
            print("👤 Admin user already exists")
    
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
