"""
Entry point for running the application directly with `python -m src`
"""

import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import setup_app

if __name__ == '__main__':
    # Set up the Flask application
    socketio, app = setup_app()
    
    # Print routes for debugging
    print("\nAvailable routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint} -> {rule}")
    
    print("\nStarting server...")
    
    # Run the application
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
