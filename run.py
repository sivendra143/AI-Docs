"""
Run the Flask application.
"""
import os
import sys
from src.app import setup_app

if __name__ == "__main__":
    # Set up the application
    socketio, app = setup_app()
    
    # Print all available routes
    print("\nAvailable routes:")
    print("-" * 50)
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule} -> {rule.methods}")
    print("-" * 50)
    
    # Run the application
    print("\nStarting server...")
    print(f"Access the application at: http://127.0.0.1:5000")
    
    if socketio:
        socketio.run(app, host="0.0.0.0", port=5000, debug=True)
    else:
        app.run(host="0.0.0.0", port=5000, debug=True)
