"""
Entry point for running the application directly with `python -m src`
"""

import os
from src import create_app, socketio

# Create the application
app, socketio = create_app()

if __name__ == '__main__':
    print("Starting application on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
