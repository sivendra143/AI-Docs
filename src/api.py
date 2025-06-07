# api.py

from flask import Flask, request, jsonify, Blueprint, send_file, current_app, make_response, send_from_directory
import os
import json
import jwt
import io
from datetime import datetime, timedelta
from functools import wraps
from flask_login import current_user, login_required
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from models import db, User, Conversation, Message
from conversation_manager import ConversationManager
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Dict, Any, Optional, List, Tuple

# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__)

# Initialize conversation manager
conversation_manager = ConversationManager()

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401
        return f(*args, **kwargs)
    return decorated

# Admin access decorator
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin privileges required', 'code': 'ADMIN_REQUIRED'}), 403
        return f(*args, **kwargs)
    return decorated

# Error handlers
@api_bp.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Resource not found', 'code': 'NOT_FOUND'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'code': 'INTERNAL_ERROR'}), 500

@api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'code': 'BAD_REQUEST'}), 400

# User routes
@api_bp.route('/users/me', methods=['GET'])
@token_required
def get_current_user() -> Dict[str, Any]:
    """Get current user's information."""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'preferred_language': current_user.preferred_language,
        'is_admin': current_user.is_admin,
        'created_at': current_user.created_at.isoformat(),
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None
    })

@api_bp.route('/users/update-language', methods=['POST'])
@token_required
def update_language() -> Tuple[Dict[str, Any], int]:
    """Update user's preferred language."""
    data = request.get_json() or {}
    language = data.get('language', 'en')
    
    if not language or len(language) != 2:
        return jsonify({'error': 'Invalid language code', 'code': 'INVALID_LANGUAGE'}), 400
    
    try:
        current_user.preferred_language = language
        current_user.last_login = datetime.utcnow()
        db.session.commit()
        return jsonify({
            'message': 'Language updated successfully',
            'preferred_language': language
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating language: {str(e)}")
        return jsonify({'error': 'Failed to update language', 'code': 'UPDATE_FAILED'}), 500

@api_bp.route('/users/update-profile', methods=['PUT'])
@token_required
def update_profile() -> Tuple[Dict[str, Any], int]:
    """Update user's profile information."""
    data = request.get_json() or {}
    
    try:
        if 'email' in data and data['email'] != current_user.email:
            # Check if email is already taken
            if User.query.filter(User.email == data['email'], User.id != current_user.id).first():
                return jsonify({'error': 'Email already in use', 'code': 'EMAIL_EXISTS'}), 400
            current_user.email = data['email']
        
        if 'current_password' in data and 'new_password' in data:
            if not check_password_hash(current_user.password, data['current_password']):
                return jsonify({'error': 'Current password is incorrect', 'code': 'INVALID_PASSWORD'}), 400
            current_user.set_password(data['new_password'])
        
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating profile: {str(e)}")
        return jsonify({'error': 'Failed to update profile', 'code': 'UPDATE_FAILED'}), 500

# Conversation routes
@api_bp.route('/conversations', methods=['GET'])
@token_required
def get_conversations() -> Tuple[Dict[str, Any], int]:
    """Get all conversations for the current user."""
    try:
        # Get query parameters
        archived = request.args.get('archived', 'false').lower() == 'true'
        limit = min(int(request.args.get('limit', '50')), 100)  # Max 100 conversations per page
        offset = max(int(request.args.get('offset', '0')), 0)
        
        # Get conversations from manager
        conversations = conversation_manager.get_user_conversations(
            user_id=current_user.id,
            archived=archived,
            limit=limit,
            offset=offset
        )
        
        # Get total count for pagination
        total = Conversation.query.filter_by(
            user_id=current_user.id, 
            is_archived=archived
        ).count()
        
        return jsonify({
            'data': conversations,
            'meta': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(conversations)) < total
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting conversations: {str(e)}")
        return jsonify({'error': 'Failed to retrieve conversations', 'code': 'RETRIEVAL_FAILED'}), 500

@api_bp.route('/conversations', methods=['POST'])
@token_required
def create_conversation() -> Tuple[Dict[str, Any], int]:
    """Create a new conversation."""
    data = request.get_json() or {}
    title = data.get('title', 'New Chat')
    
    try:
        conversation = conversation_manager.create_conversation(
            user_id=current_user.id, 
            title=title[:200]  # Limit title length
        )
        
        if not conversation:
            return jsonify({'error': 'Failed to create conversation', 'code': 'CREATION_FAILED'}), 500
            
        return jsonify({
            'id': conversation['id'],
            'title': conversation['title'],
            'created_at': conversation['created_at'],
            'message': 'Conversation created successfully'
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating conversation: {str(e)}")
        return jsonify({'error': 'Failed to create conversation', 'code': 'CREATION_FAILED'}), 500

@api_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@token_required
def get_conversation(conversation_id: int) -> Tuple[Dict[str, Any], int]:
    """Get a single conversation with its messages."""
    try:
        # Get conversation info
        conversation = conversation_manager.get_conversation(conversation_id, current_user.id)
        if not conversation:
            return jsonify({'error': 'Conversation not found', 'code': 'NOT_FOUND'}), 404
        
        # Get messages with pagination
        limit = min(int(request.args.get('limit', '50')), 100)  # Max 100 messages per request
        offset = max(int(request.args.get('offset', '0')), 0)
        
        messages = conversation_manager.get_conversation_messages(
            conversation_id=conversation_id,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        # Get total message count for pagination
        total_messages = Message.query.filter_by(conversation_id=conversation_id).count()
        
        return jsonify({
            'id': conversation['id'],
            'title': conversation['title'],
            'created_at': conversation['created_at'],
            'updated_at': conversation['updated_at'],
            'is_archived': conversation.get('is_archived', False),
            'messages': messages,
            'meta': {
                'total_messages': total_messages,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(messages)) < total_messages
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting conversation: {str(e)}")
        return jsonify({'error': 'Failed to retrieve conversation', 'code': 'RETRIEVAL_FAILED'}), 500

@api_bp.route('/conversations/<int:conversation_id>', methods=['PUT'])
@token_required
def update_conversation(conversation_id: int) -> Tuple[Dict[str, Any], int]:
    """Update a conversation's metadata."""
    data = request.get_json() or {}
    
    try:
        # Check if conversation exists and user has access
        conversation = Conversation.query.filter_by(
            id=conversation_id, 
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found', 'code': 'NOT_FOUND'}), 404
        
        # Update fields if provided
        if 'title' in data:
            conversation.title = data['title'][:200]  # Limit title length
        
        if 'is_archived' in data:
            conversation.is_archived = bool(data['is_archived'])
        
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': conversation.id,
            'title': conversation.title,
            'is_archived': conversation.is_archived,
            'updated_at': conversation.updated_at.isoformat(),
            'message': 'Conversation updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating conversation: {str(e)}")
        return jsonify({'error': 'Failed to update conversation', 'code': 'UPDATE_FAILED'}), 500

@api_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@token_required
def delete_conversation(conversation_id: int) -> Tuple[Dict[str, Any], int]:
    """Delete a conversation and all its messages."""
    try:
        success = conversation_manager.delete_conversation(conversation_id, current_user.id)
        if not success:
            return jsonify({'error': 'Conversation not found', 'code': 'NOT_FOUND'}), 404
        
        return jsonify({'message': 'Conversation deleted successfully'})
    except Exception as e:
        current_app.logger.error(f"Error deleting conversation: {str(e)}")
        return jsonify({'error': 'Failed to delete conversation', 'code': 'DELETION_FAILED'}), 500

# Message routes
@api_bp.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
@token_required
def send_message(conversation_id: int) -> Tuple[Dict[str, Any], int]:
    """Send a message in a conversation."""
    data = request.get_json() or {}
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Message content is required', 'code': 'MISSING_CONTENT'}), 400
    
    try:
        # Verify conversation exists and user has access
        conversation = Conversation.query.filter_by(
            id=conversation_id, 
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found', 'code': 'NOT_FOUND'}), 404
        
        # Add user message
        message = conversation_manager.add_message(
            conversation_id=conversation_id,
            content=content,
            is_user=True,
            language=current_user.preferred_language
        )
        
        if not message:
            return jsonify({'error': 'Failed to send message', 'code': 'MESSAGE_FAILED'}), 500
        
        # Here you would typically call your chatbot to get a response
        # For now, we'll just return the user's message
        return jsonify({
            'message': message,
            'conversation_id': conversation_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error sending message: {str(e)}")
        return jsonify({'error': 'Failed to send message', 'code': 'MESSAGE_FAILED'}), 500

# Export routes
@api_bp.route('/export/conversations/<int:conversation_id>.<string:format_type>', methods=['GET'])
@token_required
def export_conversation(conversation_id: int, format_type: str):
    """Export a conversation in the specified format (txt or pdf)."""
    if format_type not in ['txt', 'pdf']:
        return jsonify({'error': 'Unsupported export format', 'code': 'UNSUPPORTED_FORMAT'}), 400
    
    try:
        # Verify conversation exists and user has access
        conversation = Conversation.query.filter_by(
            id=conversation_id, 
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found', 'code': 'NOT_FOUND'}), 404
        
        # Get all messages ordered by creation time
        messages = Message.query.filter_by(conversation_id=conversation_id)\
                              .order_by(Message.created_at.asc())\
                              .all()
        
        if format_type == 'txt':
            return _export_txt(conversation, messages)
        else:  # pdf
            return _export_pdf(conversation, messages)
            
    except Exception as e:
        current_app.logger.error(f"Error exporting conversation: {str(e)}")
        return jsonify({'error': 'Failed to export conversation', 'code': 'EXPORT_FAILED'}), 500

def _export_txt(conversation: Conversation, messages: List[Message]) -> Any:
    """Export conversation as a text file."""
    output = []
    output.append(f"Conversation: {conversation.title}\n")
    output.append(f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.append("-" * 80 + "\n")
    
    for msg in messages:
        role = "You" if msg.is_user else "Assistant"
        timestamp = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        output.append(f"[{timestamp}] {role}:\n{msg.content}\n")
    
    response = make_response("\n".join(output))
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=conversation_{conversation.id}.txt'
    return response

def _export_pdf(conversation: Conversation, messages: List[Message]) -> Any:
    """Export conversation as a PDF file."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object, using the buffer as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=72)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#2c3e50')
    )
    
    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=24
    )
    
    user_style = ParagraphStyle(
        'User',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2980b9'),
        spaceAfter=12,
        spaceBefore=12,
        leftIndent=12,
        borderLeft=3,
        borderColor=colors.HexColor('#3498db'),
        borderWidth=1,
        borderPadding=6,
        backColor=colors.HexColor('#f8f9fa')
    )
    
    assistant_style = ParagraphStyle(
        'Assistant',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=12,
        spaceBefore=12,
        leftIndent=12,
        borderLeft=3,
        borderColor=colors.HexColor('#2ecc71'),
        borderWidth=1,
        borderPadding=6,
        backColor=colors.HexColor('#f8f9fa')
    )
    
    timestamp_style = ParagraphStyle(
        'Timestamp',
        parent=styles['Italic'],
        fontSize=8,
        textColor=colors.grey,
        spaceBefore=6
    )
    
    # Add title and metadata
    elements.append(Paragraph(conversation.title, title_style))
    elements.append(Paragraph(
        f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Last updated: {conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Messages: {len(messages)}",
        meta_style
    ))
    
    # Add messages
    for msg in messages:
        role = "You" if msg.is_user else "Assistant"
        timestamp = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        
        # Add timestamp
        elements.append(Paragraph(f"{role} - {timestamp}", timestamp_style))
        
        # Add message content with appropriate styling
        style = user_style if msg.is_user else assistant_style
        elements.append(Paragraph(msg.content.replace('\n', '<br/>'), style))
    
    # Build the PDF
    doc.build(elements)
    
    # File response
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=conversation_{conversation.id}.pdf'
    return response

# Search endpoint
@api_bp.route('/search', methods=['GET'])
@token_required
def search_messages() -> Tuple[Dict[str, Any], int]:
    """Search messages across all user's conversations."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query is required', 'code': 'MISSING_QUERY'}), 400
    
    try:
        limit = min(int(request.args.get('limit', '20')), 50)  # Max 50 results
        offset = max(int(request.args.get('offset', '0')), 0)
        
        # Search in message content
        messages = Message.query.join(Conversation).filter(
            Conversation.user_id == current_user.id,
            Message.content.ilike(f'%{query}%')
        ).order_by(Message.created_at.desc())\
         .offset(offset).limit(limit).all()
        
        # Get total count for pagination
        total = Message.query.join(Conversation).filter(
            Conversation.user_id == current_user.id,
            Message.content.ilike(f'%{query}%')
        ).count()
        
        # Format results
        results = []
        for msg in messages:
            results.append({
                'id': msg.id,
                'conversation_id': msg.conversation_id,
                'conversation_title': msg.conversation.title,
                'content': msg.content,
                'is_user': msg.is_user,
                'created_at': msg.created_at.isoformat(),
                'language': msg.language
            })
        
        return jsonify({
            'query': query,
            'results': results,
            'meta': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(results)) < total
            }
        })
    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed', 'code': 'SEARCH_FAILED'}), 500

# Statistics endpoint
@api_bp.route('/stats', methods=['GET'])
@token_required
def get_user_stats() -> Dict[str, Any]:
    """Get user statistics."""
    stats = conversation_manager.get_conversation_stats(current_user.id)
    return jsonify(stats)

def setup_api_routes(app: Flask, chatbot: Any) -> None:
    """
    Register API routes with the Flask application.
    
    Args:
        app: Flask application instance
        chatbot: Chatbot instance for handling messages
    """
    # Store chatbot instance in app config
    app.config['CHATBOT'] = chatbot
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'code': 'NOT_FOUND'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error', 'code': 'INTERNAL_ERROR'}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'code': 'BAD_REQUEST'}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'code': 'FORBIDDEN'}), 403
    
    # Add CORS headers
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
# Record query for analytics
def record_query(question, success=True):
    # This is now handled by the database
    pass

if __name__ == "__main__":
    # For testing purposes
    app = Flask(__name__)
    
    class DummyChatbot:
        def ask_question(self, question):
            return f"You asked: {question}"
            
        def get_smart_suggestions(self, question, answer):
            return ["Suggestion 1", "Suggestion 2"]
    
    dummy_chatbot = DummyChatbot()
    setup_api_routes(app, dummy_chatbot)
    
    app.run(debug=True)
