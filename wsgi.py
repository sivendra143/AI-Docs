"""
WSGI entry point for the application.
"""
import os
import sys
from src import create_app

# Add debug logging
print("Starting application...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Create and configure the application
app = create_app('development')

# Debug: Print all registered routes
print("\nRegistered routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule}")

# Import socketio after app creation to avoid circular imports
from src import socketio

if __name__ == "__main__":
    # Run the application with socketio if available
    print("\nStarting server...")
    if socketio:
        print("Using Socket.IO")
        socketio.run(app, host="0.0.0.0", port=5001, debug=True)
    else:
        print("Using standard WSGI")
        app.run(host="0.0.0.0", port=5001, debug=True)
