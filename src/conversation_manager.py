from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import desc, func, or_
from models import db, Conversation, Message, User

class ConversationManager:
    """
    A class to manage conversations and messages in the chat application.
    Handles CRUD operations for conversations and messages with proper authorization.
    """
    
    @staticmethod
    def create_conversation(user_id: int, title: str = "New Chat") -> Optional[Dict[str, Any]]:
        """
        Create a new conversation for the specified user.
        
        Args:
            user_id: The ID of the user creating the conversation
            title: The title of the conversation (default: "New Chat")
            
        Returns:
            dict: The created conversation as a dictionary or None if user doesn't exist
        """
        # Verify user exists
        if not User.query.get(user_id):
            return None
            
        conversation = Conversation(user_id=user_id, title=title)
        db.session.add(conversation)
        
        try:
            db.session.commit()
            return conversation.to_dict()
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def add_message(conversation_id: int, content: str, is_user: bool = True, 
                  language: str = 'en', tokens: int = 0) -> Optional[Dict[str, Any]]:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            content: The message content
            is_user: Whether the message is from the user (default: True)
            language: The language of the message (default: 'en')
            tokens: Number of tokens in the message (default: 0)
            
        Returns:
            dict: The created message as a dictionary or None if conversation doesn't exist
        """
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return None
            
        message = Message(
            conversation_id=conversation_id,
            content=content,
            is_user=is_user,
            language=language,
            tokens=tokens
        )
        
        # Update conversation's updated_at timestamp
        conversation.updated_at = datetime.utcnow()
        
        db.session.add(message)
        
        try:
            db.session.commit()
            return message.to_dict()
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_user_conversations(user_id: int, archived: bool = False, 
                             limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user, ordered by most recently updated.
        
        Args:
            user_id: The ID of the user
            archived: Whether to include archived conversations (default: False)
            limit: Maximum number of conversations to return (default: 50)
            offset: Number of conversations to skip (default: 0)
            
        Returns:
            list: List of conversation dictionaries
        """
        query = Conversation.query.filter_by(user_id=user_id, is_archived=archived)
        conversations = query.order_by(desc(Conversation.updated_at))\
                            .offset(offset).limit(limit).all()
        return [conv.to_dict() for conv in conversations]
    
    @staticmethod
    def get_conversation(conversation_id: int, user_id: int = None) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID, optionally verifying ownership.
        
        Args:
            conversation_id: The ID of the conversation
            user_id: Optional user ID to verify ownership
            
        Returns:
            dict: The conversation as a dictionary or None if not found/unauthorized
        """
        query = Conversation.query
        if user_id is not None:
            query = query.filter_by(id=conversation_id, user_id=user_id)
        else:
            query = query.filter_by(id=conversation_id)
            
        conversation = query.first()
        return conversation.to_dict() if conversation else None
    
    @staticmethod
    def get_conversation_messages(conversation_id: int, user_id: int = None, 
                                limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get messages for a conversation with pagination.
        
        Args:
            conversation_id: The ID of the conversation
            user_id: Optional user ID to verify ownership
            limit: Maximum number of messages to return (default: 100)
            offset: Number of messages to skip (default: 0)
            
        Returns:
            list: List of message dictionaries
        """
        # Verify the conversation exists and user has access
        query = Message.query.filter_by(conversation_id=conversation_id)
        
        if user_id is not None:
            query = query.join(Conversation).filter(Conversation.user_id == user_id)
            
        messages = query.order_by(Message.created_at.asc())\
                       .offset(offset).limit(limit).all()
        return [msg.to_dict() for msg in messages]
    
    @staticmethod
    def update_conversation(conversation_id: int, user_id: int, 
                          title: str = None, is_archived: bool = None) -> bool:
        """
        Update a conversation's metadata.
        
        Args:
            conversation_id: The ID of the conversation
            user_id: The ID of the user (for authorization)
            title: New title for the conversation (optional)
            is_archived: New archived status (optional)
            
        Returns:
            bool: True if updated, False if not found/unauthorized
        """
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        if not conversation:
            return False
            
        if title is not None:
            conversation.title = title
        if is_archived is not None:
            conversation.is_archived = is_archived
            
        conversation.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def delete_conversation(conversation_id: int, user_id: int) -> bool:
        """
        Delete a conversation and all its messages.
        
        Args:
            conversation_id: The ID of the conversation
            user_id: The ID of the user (for authorization)
            
        Returns:
            bool: True if deleted, False if not found/unauthorized
        """
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        if not conversation:
            return False
            
        try:
            # Cascade delete will handle related messages
            db.session.delete(conversation)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def search_conversations(user_id: int, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for conversations by title or message content.
        
        Args:
            user_id: The ID of the user
            query: Search query string
            limit: Maximum number of results to return (default: 20)
            
        Returns:
            list: List of matching conversation dictionaries
        """
        search = f"%{query}%"
        
        # Find conversations with matching title or messages
        conversations = db.session.query(Conversation).join(Message).filter(
            Conversation.user_id == user_id,
            or_(
                Conversation.title.ilike(search),
                Message.content.ilike(search)
            )
        ).distinct().order_by(desc(Conversation.updated_at)).limit(limit).all()
        
        return [conv.to_dict() for conv in conversations]
    
    @staticmethod
    def get_conversation_stats(user_id: int) -> Dict[str, Any]:
        """
        Get statistics about a user's conversations and messages.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            dict: Various statistics about the user's conversations
        """
        # Total conversations
        total_conv = db.session.query(func.count(Conversation.id))\
                             .filter(Conversation.user_id == user_id).scalar()
        
        # Active conversations (not archived)
        active_conv = db.session.query(func.count(Conversation.id))\
                              .filter(Conversation.user_id == user_id, 
                                     Conversation.is_archived == False).scalar()
        
        # Total messages
        total_msgs = db.session.query(func.count(Message.id))\
                             .join(Conversation)\
                             .filter(Conversation.user_id == user_id).scalar()
        
        # Tokens used (approximate)
        tokens = db.session.query(func.coalesce(func.sum(Message.tokens), 0))\
                         .join(Conversation)\
                         .filter(Conversation.user_id == user_id).scalar()
        
        # Most active conversations
        active_conversations = db.session.query(
            Conversation.id,
            Conversation.title,
            func.count(Message.id).label('message_count'),
            func.max(Message.created_at).label('last_activity')
        ).join(Message).filter(
            Conversation.user_id == user_id,
            Conversation.is_archived == False
        ).group_by(Conversation.id).order_by(
            desc('last_activity')
        ).limit(5).all()
        
        return {
            'total_conversations': total_conv,
            'active_conversations': active_conv,
            'archived_conversations': total_conv - active_conv,
            'total_messages': total_msgs,
            'total_tokens': tokens,
            'recent_activity': [{
                'id': conv.id,
                'title': conv.title,
                'message_count': conv.message_count,
                'last_activity': conv.last_activity.isoformat()
            } for conv in active_conversations]
        }
