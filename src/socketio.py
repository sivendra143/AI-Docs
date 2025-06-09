"""
Socket.IO module for the application.
This module provides a Socket.IO instance that will be configured by the Flask app.
"""
import logging
from flask_socketio import SocketIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('socketio')
logger.setLevel(logging.INFO)

# Create a Socket.IO instance with Windows-compatible settings
socketio = SocketIO(
    async_mode='threading',  # Using threading for better Windows compatibility
    cors_allowed_origins=["http://localhost:5000", "http://127.0.0.1:5000"],
    logger=logger,
    engineio_logger=logger,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1e8,  # 100MB
    path='/socket.io',
    allow_upgrades=True,
    always_connect=True,
    cors_credentials=True,
    http_compression=False,  # Simplified settings for Windows
    # Enable both polling and websocket transports
    # Polling first for compatibility, then upgrade to websocket
    transports=['polling', 'websocket']
)

# This allows other modules to import the socketio instance directly
__all__ = ['socketio']
