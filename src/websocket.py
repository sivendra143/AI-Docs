# websocket.py

from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
from flask import request, current_app, jsonify
from flask_login import current_user
from functools import wraps
from datetime import datetime
import logging
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            logger.warning("Unauthenticated WebSocket connection attempt")
            disconnect()
            return
        return f(*args, **kwargs)
    return wrapped

def setup_websocket(app, chatbot):
    """
    Set up WebSocket routes for the chatbot with conversation and language support.
    
    Args:
        app (Flask): Flask application
        chatbot: Chatbot instance
    """
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*",
        logger=app.debug,
        engineio_logger=app.debug,
        async_mode='threading',
        ping_timeout=60,
        ping_interval=25,
        max_http_buffer_size=100 * 1024 * 1024  # 100MB max message size
    )
    
    # Track active users and their conversations
    active_users = {}
    
    @socketio.on('connect')
    def handle_connect():
        if not current_user.is_authenticated:
            logger.warning("Unauthenticated WebSocket connection attempt")
            return False
            
        user_id = current_user.get_id()
        active_users[user_id] = {
            'sid': request.sid,
            'conversation_id': None,
            'last_active': datetime.utcnow(),
            'typing': False,
            'status': 'online'
        }
        logger.info(f"User {user_id} connected with SID {request.sid}")
        emit('connection_success', {
            'user_id': user_id,
            'message': 'Successfully connected to WebSocket',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        user_id = current_user.get_id()
        if user_id in active_users:
            # Notify conversation participants about user going offline
            conversation_id = active_users[user_id].get('conversation_id')
            if conversation_id:
                emit('user_status', {
                    'user_id': user_id,
                    'status': 'offline',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=conversation_id)
            
            del active_users[user_id]
            logger.info(f"User {user_id} disconnected")
    
    @socketio.on('join_conversation')
    @authenticated_only
    def handle_join_conversation(data):
        """Handle joining a conversation room."""
        conversation_id = data.get('conversation_id')
        user_id = current_user.get_id()
        
        if not conversation_id:
            emit('error', {'message': 'No conversation_id provided'})
            return
        
        # Verify user has access to this conversation
        from .models import Conversation
        conversation = Conversation.query.get(conversation_id)
        if not conversation or (conversation.user_id != user_id and not current_user.is_admin):
            emit('error', {'message': 'Access denied to this conversation'})
            return
        
        # Leave any existing conversation room
        if user_id in active_users and active_users[user_id]['conversation_id']:
            leave_room(active_users[user_id]['conversation_id'])
        
        # Join new conversation room
        join_room(conversation_id)
        active_users[user_id]['conversation_id'] = conversation_id
        active_users[user_id]['status'] = 'in_chat'
        
        logger.info(f"User {user_id} joined conversation {conversation_id}")
        
        # Load conversation history
        messages = [{
            'id': msg.id,
            'content': msg.content,
            'is_user': msg.is_user,
            'timestamp': msg.created_at.isoformat(),
            'language': msg.language or 'en'
        } for msg in conversation.messages.order_by(Message.created_at.asc()).all()]
        
        emit('conversation_joined', {
            'conversation_id': conversation_id,
            'title': conversation.title,
            'messages': messages,
            'participants': [{
                'id': user_id,
                'username': current_user.username,
                'status': 'online'
            }],
            'message': 'Successfully joined conversation',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Notify others in the conversation
        emit('user_joined', {
            'user_id': user_id,
            'username': current_user.username,
            'timestamp': datetime.utcnow().isoformat()
        }, room=conversation_id, include_self=False)
    
    @socketio.on('leave_conversation')
    @authenticated_only
    def handle_leave_conversation():
        """Handle leaving the current conversation."""
        user_id = current_user.get_id()
        if user_id in active_users and active_users[user_id]['conversation_id']:
            conversation_id = active_users[user_id]['conversation_id']
            leave_room(conversation_id)
            active_users[user_id]['conversation_id'] = None
            active_users[user_id]['status'] = 'online'
            
            emit('conversation_left', {
                'conversation_id': conversation_id,
                'message': 'Left conversation',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Notify others in the conversation
            emit('user_left', {
                'user_id': user_id,
                'username': current_user.username,
                'timestamp': datetime.utcnow().isoformat()
            }, room=conversation_id)
    
    @socketio.on('send_message')
    @authenticated_only
    def handle_send_message(data):
        """Handle sending a new message in a conversation."""
        user_id = current_user.get_id()
        conversation_id = data.get('conversation_id')
        message = data.get('message', '').strip()
        language = data.get('language', 'en')
        
        if not conversation_id:
            emit('error', {'message': 'No conversation_id provided'})
            return
            
        if not message:
            emit('error', {'message': 'Message cannot be empty'})
            return
        
        # Verify user has access to this conversation
        from .models import Conversation, Message, db
        conversation = Conversation.query.get(conversation_id)
        if not conversation or (conversation.user_id != user_id and not current_user.is_admin):
            emit('error', {'message': 'Access denied to this conversation'})
            return
        
        # Update user's active conversation and last active time
        if user_id in active_users:
            active_users[user_id]['conversation_id'] = conversation_id
            active_users[user_id]['last_active'] = datetime.utcnow()
        
        try:
            # Save user message to database
            user_msg = Message(
                conversation_id=conversation_id,
                content=message,
                is_user=True,
                language=language
            )
            db.session.add(user_msg)
            
            # Update conversation's updated_at timestamp
            conversation.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Emit the user message to the conversation room
            message_data = {
                'id': user_msg.id,
                'conversation_id': conversation_id,
                'sender': 'user',
                'user_id': user_id,
                'username': current_user.username,
                'content': message,
                'is_user': True,
                'language': language,
                'timestamp': user_msg.created_at.isoformat(),
                'status': 'delivered'
            }
            
            emit('message', message_data, room=conversation_id)
            
            # Process the message with the chatbot (in a background task)
            def process_bot_response():
                try:
                    # Get bot response
                    bot_response = chatbot.get_response(
                        message=message,
                        conversation_id=conversation_id,
                        user_id=user_id,
                        language=language
                    )
                    
                    # Save bot response to database
                    bot_msg = Message(
                        conversation_id=conversation_id,
                        content=bot_response,
                        is_user=False,
                        language=language
                    )
                    db.session.add(bot_msg)
                    db.session.commit()
                    
                    # Emit the bot response to the conversation room
                    bot_message_data = {
                        'id': bot_msg.id,
                        'conversation_id': conversation_id,
                        'sender': 'bot',
                        'content': bot_response,
                        'is_user': False,
                        'language': language,
                        'timestamp': bot_msg.created_at.isoformat(),
                        'status': 'delivered'
                    }
                    
                    socketio.emit('message', bot_message_data, room=conversation_id)
                    
                except Exception as e:
                    logger.error(f"Error processing bot response: {str(e)}")
                    socketio.emit('error', {
                        'message': 'Error generating response',
                        'details': str(e)
                    }, room=request.sid)
            
            # Process bot response in background
            socketio.start_background_task(process_bot_response)
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            emit('error', {
                'message': 'Error processing your message',
                'details': str(e)
            }, room=request.sid)
            
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
    @authenticated_only
    def handle_ask(data):
        """Handle direct questions to the chatbot."""
        try:
            user_id = current_user.get_id()
            question = data.get('question', '').strip()
            language = data.get('language', 'en')
            conversation_id = data.get('conversation_id')
            
            logger.info(f"Received ask event from user {user_id}: {question}")
            
            if not question:
                emit('error', {'message': 'Question cannot be empty'}, room=request.sid)
                return
            
            # Create a new conversation if none exists
            from .models import Conversation, Message, db
            
            try:
                if not conversation_id:
                    # Create a new conversation
                    conversation = Conversation(
                        user_id=user_id,
                        title=f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
                    )
                    db.session.add(conversation)
                    db.session.flush()  # Get the conversation ID
                    conversation_id = conversation.id
                    logger.info(f"Created new conversation: {conversation_id}")
                else:
                    # Use existing conversation
                    conversation = Conversation.query.get(conversation_id)
                    if not conversation:
                        raise ValueError(f"Conversation {conversation_id} not found")
                    logger.info(f"Using existing conversation: {conversation_id}")
                
                # Save user question
                user_msg = Message(
                    conversation_id=conversation_id,
                    content=question,
                    is_user=True,
                    language=language
                )
                db.session.add(user_msg)
                db.session.commit()
                logger.info(f"Saved user question to conversation {conversation_id}")
                
                # Define the background task for processing the question
                def process_question():
                    import time
                    start_time = time.time()
                    
                    try:
                        logger.info(f"[DEBUG] Starting to process question in conversation {conversation_id}")
                        
                        # Get conversation history for context
                        try:
                            history_messages = Message.query.filter_by(
                                conversation_id=conversation_id,
                                is_user=True
                            ).order_by(Message.created_at.desc()).limit(5).all()
                            logger.info(f"[DEBUG] Retrieved {len(history_messages)} history messages")
                            
                            # Format conversation history (oldest first)
                            conversation_history = [
                                {
                                    'content': msg.content,
                                    'is_user': msg.is_user,
                                    'created_at': msg.created_at.isoformat()
                                }
                                for msg in reversed(history_messages)
                            ]
                        except Exception as e:
                            logger.error(f"[ERROR] Error getting conversation history: {str(e)}", exc_info=True)
                            conversation_history = []
                        
                        # Get response from chatbot with timeout
                        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
                        
                        def get_chatbot_response():
                            return chatbot.ask_question(
                                question=question,
                                language=language,
                                conversation_history=conversation_history
                            )
                        
                        # Run with timeout
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(get_chatbot_response)
                            try:
                                bot_response = future.result(timeout=45)  # 45 second timeout
                                logger.info(f"[DEBUG] Successfully got bot response in {time.time() - start_time:.2f} seconds")
                                
                                if not bot_response:
                                    logger.warning("[WARNING] Empty response from chatbot.get_response")
                                    bot_response = "I'm sorry, I couldn't generate a response. Please try again."
                                
                                # Save bot response
                                logger.info("[DEBUG] Saving bot response to database...")
                                try:
                                    bot_msg = Message(
                                        conversation_id=conversation_id,
                                        content=bot_response,
                                        is_user=False,
                                        language=language
                                    )
                                    db.session.add(bot_msg)
                                    db.session.commit()
                                    logger.info("[DEBUG] Successfully saved bot response to database")
                                    
                                    # Prepare response data
                                    response_data = {
                                        'conversation_id': conversation_id,
                                        'response': bot_response,
                                        'timestamp': datetime.utcnow().isoformat(),
                                        'status': 'success'
                                    }
                                    
                                    # Emit the response
                                    logger.info(f"[DEBUG] Sending ask_response event with data: {response_data}")
                                    socketio.emit('ask_response', response_data, room=request.sid)
                                    logger.info("[DEBUG] ask_response event sent")
                                    
                                    return response_data
                                    
                                except Exception as e:
                                    error_msg = f"Error saving bot response: {str(e)}"
                                    logger.error(f"[ERROR] {error_msg}", exc_info=True)
                                    socketio.emit('error', {'message': error_msg}, room=request.sid)
                                    return {'status': 'error', 'message': error_msg}
                                
                            except FutureTimeoutError:
                                error_msg = "The request timed out. Please try again with a different question."
                                logger.error(f"[ERROR] {error_msg}")
                                socketio.emit('error', {'message': error_msg}, room=request.sid)
                                return {'status': 'error', 'message': error_msg}
                                
                            except Exception as e:
                                error_msg = f"Error getting response from chatbot: {str(e)}"
                                logger.error(f"[ERROR] {error_msg}", exc_info=True)
                                socketio.emit('error', {'message': error_msg}, room=request.sid)
                                return {'status': 'error', 'message': error_msg}
                        
                    except Exception as e:
                        error_msg = f"Unexpected error in process_question: {str(e)}"
                        logger.error(f"[CRITICAL] {error_msg}", exc_info=True)
                        socketio.emit('error', {'message': error_msg}, room=request.sid)
                        return {'status': 'error', 'message': error_msg}
                
                # Start processing the question in a background task
                socketio.start_background_task(process_question)
                
                # Immediately acknowledge the question was received and is being processed
                return {
                    'status': 'processing', 
                    'conversation_id': conversation_id,
                    'message': 'Your question is being processed.'
                }
                
            except Exception as e:
                error_msg = f"Error in handle_ask (inner): {str(e)}"
                logger.error(error_msg, exc_info=True)
                emit('error', {
                    'message': 'Error processing your question',
                    'details': str(e)
                }, room=request.sid)
                return {'status': 'error', 'message': str(e)}
                
        except Exception as e:
            error_msg = f"Error in handle_ask (outer): {str(e)}"
            logger.error(error_msg, exc_info=True)
            emit('error', {
                'message': 'An unexpected error occurred',
                'details': str(e)
            }, room=request.sid)
            return {'status': 'error', 'message': str(e)}
    
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
    
    @socketio.on('disconnect')
    def handle_disconnect():
        if request.sid in active_users:
            user_id = active_users[request.sid]['user_id']
            logger.info(f"User {user_id} disconnected")
            del active_users[request.sid]
        else:
            logger.info("Unknown client disconnected")
    
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
        return 'WebSocket Server is running!'
        
    socketio = setup_websocket(app, dummy_chatbot)
    
    # Run the app with socketio on port 5000
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
