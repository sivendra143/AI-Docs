"""
WSGI entry point for the application.
"""
import os
import sys
from pathlib import Path
from src import create_app
from src.websocket import setup_websocket

# Add debug logging
print("\n" + "=" * 50)
print(">> Starting AI Document Chat Application")
print("=" * 50)
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Absolute path to src: {os.path.abspath('src')}")
print(f"Absolute path to static: {os.path.abspath('src/static')}")

# Create and configure the application
app = create_app('development')

# Ensure static URL path is set correctly
app.static_url_path = '/static'
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'static')
print(f"Static folder: {app.static_folder}")
print(f"Static URL path: {app.static_url_path}")

# Configure CORS for the entire app
from flask_cors import CORS
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Setup WebSocket with enhanced configuration
socketio = setup_websocket(app)

# Additional Socket.IO configuration
# Using threading mode for Windows compatibility
socketio.init_app(app, 
                 cors_allowed_origins=["http://localhost:5000", "http://127.0.0.1:5000"],
                 async_mode='threading',  # Using threading for Windows compatibility
                 logger=True,
                 engineio_logger=True,
                 ping_timeout=60,
                 ping_interval=25,
                 path='/socket.io',
                 allow_upgrades=True,
                 cors_credentials=True)

# Get socketio from app extensions
socketio = app.extensions.get('socketio')

if not socketio:
    raise RuntimeError("Socket.IO not properly initialized in the application")

# Enable detailed logging
socketio.server.eio.logger = True

print("\n🔌 WebSocket server configured")
print(f"   - Async Mode: {socketio.async_mode}")
print(f"   - Path: {socketio.server_options.get('path', '/socket.io')}")
print(f"   - Transports: {socketio.server_options.get('transports', ['websocket', 'polling'])}")
print(f"   - CORS Allowed Origins: {app.config.get('CORS_ALLOWED_ORIGINS', '*')}")

if __name__ == "__main__":
    # Run the application with socketio
    print("\n🌐 Starting WebSocket server...")
    print(f"   - Host: 0.0.0.0")
    print(f"   - Port: 5000")
    print(f"   - Debug: {app.debug}")
    print("\n🔌 WebSocket server is running. Press Ctrl+C to stop.")
    
    try:
        socketio.run(
            app,
            host="0.0.0.0",
            port=5000,
            debug=app.debug,
            use_reloader=True,
            log_output=True,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise
