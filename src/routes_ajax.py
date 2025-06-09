"""
Simple AJAX routes for chat fallback when WebSockets are unavailable.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_required
import datetime
import uuid

# Create blueprint
ajax_bp = Blueprint('ajax_bp', __name__, url_prefix='/api')

@ajax_bp.route('/chat/message', methods=['POST'])
@login_required
def process_message():
    """Handle chat messages via AJAX instead of WebSockets"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing message'}), 400
            
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', f'user_{current_user.id}_ajax_{uuid.uuid4()}')
        
        # Get chatbot instance from app extensions
        chatbot = current_app.extensions.get('chatbot')
        if not chatbot:
            return jsonify({
                'message': 'Sorry, the chatbot is not available right now.',
                'error': 'Chatbot not initialized'
            }), 500
        
        # Process the message - this would normally be async with WebSockets
        # Here we'll just do a simple synchronous call
        try:
            # For AJAX fallback, we'll process directly
            response = "I've received your message. This is a simple AJAX fallback since WebSocket is temporarily unavailable."
            
            return jsonify({
                'message': response,
                'conversation_id': conversation_id,
                'timestamp': datetime.datetime.utcnow().isoformat()
            })
        except Exception as e:
            current_app.logger.error(f"Error processing message: {str(e)}")
            return jsonify({
                'message': 'Sorry, I encountered an error while processing your message.',
                'error': str(e)
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error in AJAX chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500
