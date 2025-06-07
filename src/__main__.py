"""
Entry point for running the application directly with `python -m src`
"""

from .app import app, socketio

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
