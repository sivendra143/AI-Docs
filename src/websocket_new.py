from flask import request, current_app
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

def setup_websocket(app, chatbot=None):
    """Set up WebSocket event handlers."""
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        logger=app.debug,
        engineio_logger=app.debug,
        async_mode='threading'
    )
    
    # Store chatbot instance in app context
    if chatbot:
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['chatbot'] = chatbot
    
    # Track active users
    active_users = {}
    
    def authenticated_only(f):
        """Decorator to ensure user is authenticated for protected routes."""
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            return f(*args, **kwargs)
        return wrapped
    
    @socketio.on('connect')
    def handle_connect():
        """Handle new WebSocket connection."""
        logger.info(f"Client connected: {request.sid}")
        
        # If user is authenticated, add to active users
        if current_user.is_authenticated:
            user_id = current_user.get_id()
            active_users[user_id] = {
                'sid': request.sid,
                'last_active': datetime.utcnow()
            }
            logger.info(f"Authenticated user {user_id} connected")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle WebSocket disconnection."""
        logger.info(f"Client disconnected: {request.sid}")
        
        # Remove from active users if authenticated
        if current_user.is_authenticated:
            user_id = current_user.get_id()
            if user_id in active_users:
                del active_users[user_id]
                logger.info(f"User {user_id} disconnected")
    
    @socketio.on('typing')
    @authenticated_only
    def handle_typing(data):
        """Handle typing indicators."""
        user_id = current_user.get_id()
        conversation_id = data.get('conversation_id')
        is_typing = data.get('is_typing', False)
        
        if not conversation_id or user_id not in active_users:
            return
        
        active_users[user_id]['typing'] = is_typing
        active_users[user_id]['last_active'] = datetime.utcnow()
        
        # Notify others in the conversation
        emit('user_typing', {
            'user_id': user_id,
            'username': current_user.username,
            'is_typing': is_typing,
            'timestamp': datetime.utcnow().isoformat()
        }, room=conversation_id, include_self=False)
    
    @socketio.on('ask')
    def handle_ask(data):
        """Handle questions to the chatbot with RAG integration."""
        conversation_id = None
        try:
            # Get user info
            user_id = 'anonymous'
            username = 'Guest'
            if current_user.is_authenticated:
                user_id = current_user.get_id()
                username = current_user.username
                
            question = data.get('question', '').strip()
            language = data.get('language', 'en')
            conversation_id = data.get('conversation_id')
            
            logger.info(f"[DEBUG] Received ask event from user {user_id}: {question}")
            
            if not question:
                emit('error', {'message': 'Question cannot be empty'}, room=request.sid)
                return
            
            # Get the chatbot instance from the app context
            if not hasattr(current_app, 'extensions') or 'chatbot' not in current_app.extensions:
                logger.error("Chatbot not found in app extensions")
                emit('error', {'message': 'Chatbot not initialized. Please try again later.'}, room=request.sid)
                return
                
            chatbot = current_app.extensions['chatbot']
            from .models import Conversation, Message, db
            
            try:
                # Get or create conversation
                conversation = None
                if conversation_id:
                    conversation = Conversation.query.get(conversation_id)
                    if not conversation:
                        raise ValueError(f"Conversation {conversation_id} not found")
                    logger.info(f"[DEBUG] Using existing conversation: {conversation_id}")
                elif current_user.is_authenticated:
                    # For authenticated users, create a new conversation
                    conversation = Conversation(
                        user_id=user_id,
                        title=f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
                    )
                    db.session.add(conversation)
                    db.session.flush()
                    conversation_id = conversation.id
                    logger.info(f"[DEBUG] Created new conversation: {conversation_id}")
                
                # Save user message if we have a conversation
                if conversation:
                    user_msg = Message(
                        conversation_id=conversation_id,
                        content=question,
                        is_user=True,
                        language=language
                    )
                    db.session.add(user_msg)
                    conversation.updated_at = datetime.utcnow()
                    db.session.commit()
                
                # Emit the user message
                emit('message', {
                    'sender': 'user',
                    'username': username,
                    'content': question,
                    'timestamp': datetime.utcnow().isoformat(),
                    'is_user': True
                })
                
                # Process the question with the chatbot in a background task
                def process_question():
                    try:
                        logger.info(f"[DEBUG] Starting to process question in conversation {conversation_id}")
                        
                        # Get conversation history if available
                        conversation_history = []
                        if conversation:
                            conversation_history = [{
                                'content': msg.content,
                                'is_user': msg.is_user,
                                'created_at': msg.created_at.isoformat()
                            } for msg in conversation.messages.order_by(Message.created_at.desc()).limit(5).all()]
                            conversation_history.reverse()  # Oldest first
                        
                        # Get response from chatbot
                        bot_response = chatbot.ask_question(
                            question=question,
                            language=language,
                            conversation_history=conversation_history
                        )
                        
                        # Save bot response if we have a conversation
                        if conversation:
                            bot_msg = Message(
                                conversation_id=conversation.id,
                                content=bot_response,
                                is_user=False,
                                language=language
                            )
                            db.session.add(bot_msg)
                            conversation.updated_at = datetime.utcnow()
                            db.session.commit()
                        
                        # Emit the bot response
                        socketio.emit('answer', {
                            'answer': bot_response,
                            'suggestions': [
                                "Can you elaborate on that?",
                                "Tell me more about this topic",
                                "Can you provide more details?"
                            ]
                        })
                        
                    except Exception as e:
                        logger.error(f"[ERROR] Error in process_question: {str(e)}", exc_info=True)
                        socketio.emit('error', {
                            'message': 'Error generating response',
                            'details': str(e)
                        }, room=request.sid)
                
                # Start processing in background
                socketio.start_background_task(process_question)
                
                # Return conversation ID to client if available
                if conversation_id:
                    return {'status': 'processing', 'conversation_id': conversation_id}
                return {'status': 'processing'}
                
            except Exception as e:
                logger.error(f"[ERROR] Error handling ask event: {str(e)}", exc_info=True)
                emit('error', {
                    'message': f'Error processing your request: {str(e)}',
                    'conversation_id': conversation_id
                }, room=request.sid)
                
        except Exception as e:
            logger.error(f"[ERROR] Unhandled exception in handle_ask: {str(e)}", exc_info=True)
            emit('error', {
                'message': 'An unexpected error occurred',
                'conversation_id': conversation_id
            }, room=request.sid)
    
    @socketio.on('message_status')
    @authenticated_only
    def handle_message_status(data):
        """Update message status (delivered, read, etc.)."""
        message_id = data.get('message_id')
        status = data.get('status')
        
        if not message_id or not status:
            return
        
        from .models import Message, db
        message = Message.query.get(message_id)
        
        if message and message.conversation.user_id == current_user.id:
            # Update message status logic here
            # For example, mark as read
            if status == 'read':
                message.read_at = datetime.utcnow()
                db.session.commit()
                
                # Notify sender that message was read
                emit('message_status_updated', {
                    'message_id': message_id,
                    'status': 'read',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=message.conversation_id)
    
    @socketio.on('request_conversation_history')
    @authenticated_only
    def handle_request_history(data):
        """Handle request for conversation history."""
        conversation_id = data.get('conversation_id')
        limit = min(int(data.get('limit', 50)), 100)  # Max 100 messages
        
        if not conversation_id:
            emit('error', {'message': 'No conversation_id provided'})
            return
        
        from .models import Conversation, Message
        conversation = Conversation.query.get(conversation_id)
        
        if not conversation or conversation.user_id != current_user.id:
            emit('error', {'message': 'Access denied to this conversation'})
            return
        
        # Get messages with pagination
        messages = Message.query.filter_by(conversation_id=conversation_id)\
            .order_by(Message.created_at.desc())\
            .limit(limit)\
            .all()
        
        # Format messages
        formatted_messages = [{
            'id': msg.id,
            'content': msg.content,
            'is_user': msg.is_user,
            'timestamp': msg.created_at.isoformat(),
            'language': msg.language or 'en',
            'status': 'read' if msg.read_at else 'delivered'
        } for msg in reversed(messages)]  # Reverse to get chronological order
        
        emit('conversation_history', {
            'conversation_id': conversation_id,
            'messages': formatted_messages,
            'has_more': len(messages) >= limit
        })
    
    return socketio

def create_test_app():
    from flask import Flask
    from flask_login import LoginManager, UserMixin
    from flask_sqlalchemy import SQLAlchemy
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db = SQLAlchemy(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    # Dummy user model for testing
    class User(UserMixin):
        def __init__(self, id, username='testuser'):
            self.id = id
            self.username = username
            self.preferred_language = 'en'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User(user_id)
    
    # Dummy chatbot for testing
    class DummyChatbot:
        def ask_question(self, question, language='en', conversation_history=None):
            return f"Answer to: {question} (Language: {language})"
            
        def get_smart_suggestions(self, previous_question, context, language='en'):
            return [
                f"Tell me more about {previous_question.split()[0]} (Language: {language})",
                f"How does {previous_question} work?",
                "Can you explain further?"
            ]
    
    return app, DummyChatbot()

if __name__ == "__main__":
    # For testing WebSocket server
    app, dummy_chatbot = create_test_app()
    
    @app.route('/')
    def index():
        return "WebSocket Test Server"
    
    socketio = setup_websocket(app, dummy_chatbot)
    
    # Run the app with socketio
    socketio.run(app, debug=True, port=5000)
