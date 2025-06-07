# websocket.py

from flask_socketio import SocketIO, emit, disconnect
from flask import request
import jwt
import functools
import json

# Secret key for JWT (should match the one in api.py)
SECRET_KEY = "your-secret-key-change-this-in-production"

def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not request.args.get('token'):
            # Allow non-authenticated connections for public chat
            return f(*args, **kwargs)
        
        try:
            token = request.args.get('token')
            # Verify token
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return f(*args, **kwargs)
        except:
            disconnect()
    return wrapped

def setup_websocket(app, chatbot):
    """
    Set up WebSocket routes for the chatbot.
    
    Args:
        app (Flask): Flask application
        chatbot: Chatbot instance
    """
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    @socketio.on('connect')
    def handle_connect():
        emit('connected', {'status': 'connected'})
    
    @socketio.on('ask')
    @authenticated_only
    def handle_ask(data):
        question = data.get('question', '')
        
        if not question:
            emit('answer', {
                'answer': "Please ask a question.",
                'suggestions': []
            })
            return
        
        try:
            answer = chatbot.ask_question(question)
            suggestions = chatbot.get_smart_suggestions(question, answer)
            
            # Record query for analytics (if available)
            try:
                from api import record_query
                record_query(question, True)
            except ImportError:
                pass
            
            emit('answer', {
                'answer': answer,
                'suggestions': suggestions
            })
        except Exception as e:
            # Record failed query for analytics (if available)
            try:
                from api import record_query
                record_query(question, False)
            except ImportError:
                pass
                
            emit('answer', {
                'answer': f"Error: {str(e)}",
                'suggestions': []
            })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
    
    return socketio

if __name__ == "__main__":
    # For testing purposes
    from flask import Flask
    
    app = Flask(__name__)
    
    class DummyChatbot:
        def ask_question(self, question):
            return f"Answer to: {question}"
            
        def get_smart_suggestions(self, question, answer):
            return ["Tell me more", "How does this work?", "Can you explain further?"]
    
    dummy_chatbot = DummyChatbot()
    socketio = setup_websocket(app, dummy_chatbot)
    
    socketio.run(app, debug=True)

