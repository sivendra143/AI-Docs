# api.py

from flask import Flask, request, jsonify, Blueprint
import json
import jwt
from datetime import datetime, timedelta
from functools import wraps

# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__)

# Secret key for JWT
SECRET_KEY = "your-secret-key-change-this-in-production"

# User database (replace with a real database in production)
USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin"
    },
    "user": {
        "password": "user123",
        "role": "user"
    }
}

# Analytics storage
analytics = {
    "queries": [],
    "top_queries": {},
    "total_queries": 0,
    "successful_queries": 0,
    "failed_queries": 0
}

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            # Decode token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data['username']
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

# Admin access decorator
def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if USERS.get(current_user, {}).get('role') != 'admin':
            return jsonify({'message': 'Admin privileges required!'}), 403
        return f(current_user, *args, **kwargs)
    
    return decorated

# Login route
@api_bp.route('/login', methods=['POST'])
def login():
    auth = request.json
    
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Could not verify'}), 401
    
    username = auth.get('username')
    password = auth.get('password')
    
    if username not in USERS or USERS[username]['password'] != password:
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Generate token
    token = jwt.encode({
        'username': username,
        'role': USERS[username]['role'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY)
    
    return jsonify({'token': token})

# Protected route example
@api_bp.route('/protected', methods=['GET'])
@token_required
def protected(current_user):
    return jsonify({'message': f'Hello, {current_user}!'})

# Admin analytics route
@api_bp.route('/analytics', methods=['GET'])
@token_required
@admin_required
def get_analytics(current_user):
    return jsonify(analytics)

# Record query for analytics
def record_query(question, success=True):
    analytics['total_queries'] += 1
    
    if success:
        analytics['successful_queries'] += 1
    else:
        analytics['failed_queries'] += 1
    
    # Record query
    analytics['queries'].append({
        'question': question,
        'timestamp': datetime.now().isoformat(),
        'success': success
    })
    
    # Update top queries
    if question in analytics['top_queries']:
        analytics['top_queries'][question] += 1
    else:
        analytics['top_queries'][question] = 1

def setup_api_routes(app, chatbot):
    """
    Set up API routes for the chatbot.
    
    Args:
        app (Flask): Flask application
        chatbot: Chatbot instance
    """
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.route('/api/ask', methods=['POST'])
    # @token_required  # Temporarily disabled for testing
    def api_ask():
        # current_user = 'demo'  # Set a default user for testing
        data = request.json
        question = data.get('question', '')
        
        if not question:
            record_query(question, False)
            return jsonify({
                'answer': "Please ask a question.",
                'suggestions': []
            })
        
        try:
            answer = chatbot.ask_question(question)
            suggestions = chatbot.get_smart_suggestions(question, answer)
            
            record_query(question, True)
            
            return jsonify({
                'answer': answer,
                'suggestions': suggestions
            })
        except Exception as e:
            record_query(question, False)
            return jsonify({
                'error': str(e)
            }), 500

if __name__ == "__main__":
    # For testing purposes
    app = Flask(__name__)
    
    class DummyChatbot:
        def ask_question(self, question):
            return f"Answer to: {question}"
            
        def get_smart_suggestions(self, question, answer):
            return ["Tell me more", "How does this work?", "Can you explain further?"]
    
    dummy_chatbot = DummyChatbot()
    setup_api_routes(app, dummy_chatbot)
    
    app.run(debug=True)

