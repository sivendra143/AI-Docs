from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from src.extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    preferred_language = db.Column(db.String(10), default='en')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)
    
    def get_id(self):
        """Return the user ID as a string."""
        return str(self.id)
    
    def __repr__(self):
        return f'<User {self.username}>'

from src.extensions import login_manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, default="New Chat")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    is_archived = db.Column(db.Boolean, default=False, index=True)
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan', order_by='Message.created_at.asc()')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': len(self.messages)
        }
    
    def __repr__(self):
        return f'<Conversation {self.id} - {self.title}>'


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True, index=True)
    language = db.Column(db.String(10), default='en')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    tokens = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'content': self.content,
            'is_user': self.is_user,
            'language': self.language,
            'created_at': self.created_at.isoformat(),
            'tokens': self.tokens
        }
    
    def __repr__(self):
        return f'<Message {self.id} - {self.content[:50]}>'


class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    size = db.Column(db.Integer, default=0)  # Size in bytes
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_processed = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref='documents', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'size': self.size,
            'user_id': self.user_id,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'is_processed': self.is_processed,
            'is_public': self.is_public
        }
    
    def __repr__(self):
        return f'<Document {self.id} - {self.filename}>'
