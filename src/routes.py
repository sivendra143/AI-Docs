from flask import Blueprint, render_template, redirect, url_for, jsonify, request, current_app, send_from_directory, send_file
from flask_login import login_required, current_user, login_user, logout_user, login_fresh
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from .models import User, Conversation, Message, db

# Create blueprints with unique names to prevent duplicate registration
api_bp = Blueprint('api_bp', __name__)
root_bp = Blueprint('root_bp', __name__)

# Test route to check if the root blueprint is working
@root_bp.route('/test')
def test():
    return "Test route is working!"

# Root route for serving the main UI
@root_bp.route('/')
def index():
    try:
        # Debug: Print current user info
        print(f"Current user: {current_user}")
        print(f"Is authenticated: {current_user.is_authenticated}")
        
        # Check if templates exist
        import os
        from flask import current_app
        
        print("Template folder:", current_app.template_folder)
        print("Index template exists:", os.path.exists(os.path.join(current_app.template_folder, 'index.html')))
        print("Login template exists:", os.path.exists(os.path.join(current_app.template_folder, 'login.html')))
        
        if current_user.is_authenticated:
            return render_template('index.html')
        return render_template('login.html')
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in root route: {error_details}")
        return f"Error: {str(e)}\n\n{error_details}", 500

# Admin dashboard route
@root_bp.route('/admin')
@login_required
def admin_dashboard():
    if not getattr(current_user, 'is_admin', False):
        return "Unauthorized", 403
    return render_template('admin.html')

# Login page route (renders login.html)
@root_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# Admin API: List all users (for admin dashboard)
@api_bp.route('/admin/users', methods=['GET'])
@login_required
def admin_list_users():
    if not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Forbidden', 'message': 'Admin access required'}), 403
    users = User.query.all()
    user_list = [
        {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'is_admin': u.is_admin,
            'preferred_language': u.preferred_language,
            'last_login': u.last_login.isoformat() if u.last_login else None,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'is_active': u.is_active
        } for u in users
    ]
    return jsonify({'users': user_list})

# Admin API: Promote user to admin
@api_bp.route('/admin/user/<int:user_id>/promote', methods=['POST'])
@login_required
def admin_promote_user(user_id):
    if not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Forbidden', 'message': 'Admin access required'}), 403
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user.is_admin = True
    db.session.commit()
    return jsonify({'success': True, 'message': 'User promoted to admin'})

# Admin API: Demote user from admin
@api_bp.route('/admin/user/<int:user_id>/demote', methods=['POST'])
@login_required
def admin_demote_user(user_id):
    if not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Forbidden', 'message': 'Admin access required'}), 403
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if user.id == current_user.id:
        return jsonify({'error': 'You cannot demote yourself'}), 400
    user.is_admin = False
    db.session.commit()
    return jsonify({'success': True, 'message': 'User demoted from admin'})

# Admin API: Delete user
@api_bp.route('/admin/user/<int:user_id>/delete', methods=['DELETE'])
@login_required
def admin_delete_user(user_id):
    if not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Forbidden', 'message': 'Admin access required'}), 403
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if user.id == current_user.id:
        return jsonify({'error': 'You cannot delete yourself'}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'User deleted'})

# Admin API: List all documents
@api_bp.route('/admin/documents', methods=['GET'])
@login_required
def admin_list_documents():
    if not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Forbidden', 'message': 'Admin access required'}), 403
    from .models import Conversation  # Adjust if you have a Document model
    # If you have a Document model, use Document.query.all()
    # Here, we use Conversation as a placeholder for document metadata
    docs = []
    try:
        from .models import Document
        docs = Document.query.all()
        doc_list = [
            {
                'id': d.id,
                'filename': getattr(d, 'filename', ''),
                'uploaded_at': getattr(d, 'uploaded_at', None),
                'owner': getattr(d, 'user_id', None),
                'size': getattr(d, 'size', None)
            } for d in docs
        ]
    except ImportError:
        # If Document model doesn't exist, fallback to empty
        doc_list = []
    return jsonify({'documents': doc_list})

# Admin API: Delete document
@api_bp.route('/admin/document/<int:doc_id>/delete', methods=['DELETE'])
@login_required
def admin_delete_document(doc_id):
    if not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Forbidden', 'message': 'Admin access required'}), 403
    try:
        from .models import Document
        doc = Document.query.get(doc_id)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        db.session.delete(doc)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Document deleted'})
    except ImportError:
        return jsonify({'error': 'Document model not found'}), 500

# Admin API: Analytics summary
@api_bp.route('/admin/analytics', methods=['GET'])
@login_required
def admin_analytics():
    import datetime
    if not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Forbidden', 'message': 'Admin access required'}), 403
    user_count = User.query.count()
    try:
        from .models import Document
        doc_count = Document.query.count()
    except ImportError:
        doc_count = 0
        Document = None
    from .models import Conversation, Message
    chat_count = Conversation.query.count() if Conversation else 0
    message_count = Message.query.count() if Message else 0
    # Time-series: last 8 months
    now = datetime.datetime.utcnow()
    months = [(now - datetime.timedelta(days=30*i)).strftime('%Y-%m') for i in reversed(range(8))]
    # User growth
    user_growth = {m: 0 for m in months}
    if hasattr(User, 'created_at'):
        for u in User.query.all():
            if u.created_at:
                m = u.created_at.strftime('%Y-%m')
                if m in user_growth: user_growth[m] += 1
    else:
        # Fallback dummy data
        vals = [2, 3, 4, 7, 10, 15, 18, user_count]
        for i, m in enumerate(months):
            user_growth[m] = vals[i] if i < len(vals) else user_count
    # Document growth
    document_growth = {m: 0 for m in months}
    if Document and hasattr(Document, 'uploaded_at'):
        for d in Document.query.all():
            if getattr(d, 'uploaded_at', None):
                m = d.uploaded_at.strftime('%Y-%m')
                if m in document_growth: document_growth[m] += 1
    else:
        # Fallback dummy data
        vals = [0, 1, 1, 2, 2, 3, 4, doc_count]
        for i, m in enumerate(months):
            document_growth[m] = vals[i] if i < len(vals) else doc_count
    # Top 5 most active users
    top_users = []
    try:
        from .models import Message
        from sqlalchemy import func
        top = (
            db.session.query(User.id, User.username, User.email, func.count(Message.id).label('message_count'))
            .join(Message, Message.user_id == User.id)
            .group_by(User.id)
            .order_by(func.count(Message.id).desc())
            .limit(5)
            .all()
        )
        for u in top:
            top_users.append({'id': u.id, 'username': u.username, 'email': u.email, 'message_count': u.message_count})
    except Exception:
        # Fallback dummy data
        top_users = [
            {'id': 1, 'username': 'admin', 'email': 'admin@example.com', 'message_count': 22},
            {'id': 2, 'username': 'test', 'email': 'test@example.com', 'message_count': 12}
        ]
    return jsonify({
        'users': user_count,
        'documents': doc_count,
        'conversations': chat_count,
        'messages': message_count,
        'user_growth': user_growth,
        'document_growth': document_growth,
        'top_users': top_users
    })

# Helper function to get allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Auth Routes
@api_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('root_bp.index'))
        return render_template('login.html')
        
    if current_user.is_authenticated:
        return jsonify({'success': True, 'redirect': url_for('root_bp.index')})
    
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_admin': user.is_admin,
                    'preferred_language': user.preferred_language or 'en'
                }
            })
        
        return jsonify({
            'success': False,
            'message': 'Invalid username or password'
        }), 401
    
    return jsonify({'message': 'Please log in'})

@api_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@api_bp.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Already logged in'}), 400
    
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    user = User(
        username=username,
        email=email,
        preferred_language=data.get('preferred_language', 'en')
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    
    return jsonify({
        'success': True,
        'message': 'Registration successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'preferred_language': user.preferred_language
        }
    }), 201

# User Routes
@api_bp.route('/users/me', methods=['GET'])
@login_required
def get_current_user_info():
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'is_admin': current_user.is_admin,
        'preferred_language': current_user.preferred_language or 'en',
        'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None
    })

@api_bp.route('/users/update-language', methods=['POST'])
@login_required
def update_user_language():
    data = request.get_json()
    language = data.get('language', 'en')
    
    current_user.preferred_language = language
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Language updated successfully',
        'preferred_language': language
    })

# Chat Routes
@api_bp.route('/chat/history', methods=['GET'])
@login_required
def get_chat_history():
    conversations = Conversation.query.filter_by(user_id=current_user.id, is_archived=False)\
        .order_by(Conversation.updated_at.desc()).all()
    
    return jsonify([{
        'id': conv.id,
        'title': conv.title,
        'created_at': conv.created_at.isoformat(),
        'updated_at': conv.updated_at.isoformat(),
        'message_count': len(conv.messages)
    } for conv in conversations])

@api_bp.route('/chat/new', methods=['POST'])
@login_required
def new_chat():
    data = request.get_json()
    title = data.get('title', 'New Chat')
    
    conversation = Conversation(user_id=current_user.id, title=title)
    db.session.add(conversation)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'conversation_id': conversation.id,
        'title': conversation.title
    }), 201

@api_bp.route('/chat/<int:conversation_id>', methods=['GET', 'DELETE'])
@login_required
def manage_conversation(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    
    if conversation.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if request.method == 'DELETE':
        conversation.is_archived = True
        db.session.commit()
        return jsonify({'success': True, 'message': 'Conversation archived'})
    
    # GET request - return conversation details
    messages = Message.query.filter_by(conversation_id=conversation_id)\
        .order_by(Message.created_at.asc()).all()
    
    return jsonify({
        'id': conversation.id,
        'title': conversation.title,
        'created_at': conversation.created_at.isoformat(),
        'updated_at': conversation.updated_at.isoformat(),
        'messages': [{
            'id': msg.id,
            'content': msg.content,
            'is_user': msg.is_user,
            'created_at': msg.created_at.isoformat(),
            'language': msg.language
        } for msg in messages]
    })

# Document Routes
@api_bp.route('/documents/upload', methods=['POST'])
@login_required
def upload_document():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Save document to database
        try:
            file_type = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
            file_size = os.path.getsize(filepath)
            
            from .models import Document
            doc = Document(
                filename=filename,
                file_path=filepath,
                file_type=file_type,
                size=file_size,
                user_id=current_user.id,
                uploaded_at=datetime.utcnow(),
                is_processed=False
            )
            db.session.add(doc)
            db.session.commit()
            
            # Process the document if processor is available
            processor = current_app.config.get('document_processor')
            if processor:
                processor.process_documents()
            
            return jsonify({
                'success': True,
                'message': 'File uploaded successfully',
                'filename': filename,
                'document_id': doc.id
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error saving document to database: {str(e)}'
            }), 500
    
    return jsonify({
        'success': False,
        'message': 'File type not allowed. Allowed types: ' + 
                  ', '.join(current_app.config['ALLOWED_EXTENSIONS'])
    }), 400

@api_bp.route('/documents/list')
@login_required
def list_documents():
    try:
        from .models import Document
        # Get documents for current user or public documents
        documents = Document.query.filter(
            (Document.user_id == current_user.id) | (Document.is_public == True)
        ).all()
        
        doc_list = []
        for doc in documents:
            doc_list.append({
                'id': doc.id,
                'name': doc.filename,
                'size': doc.size,
                'modified': doc.uploaded_at.timestamp() if doc.uploaded_at else 0,
                'type': doc.file_type,
                'processed': doc.is_processed
            })
        
        return jsonify(doc_list)
    except Exception as e:
        print(f"Error listing documents: {e}")
        # Fallback to file system if database query fails
        docs_folder = current_app.config.get('DOCS_FOLDER', 'docs')
        if not os.path.exists(docs_folder):
            return jsonify([])
        
        files = []
        for filename in os.listdir(docs_folder):
            path = os.path.join(docs_folder, filename)
            if os.path.isfile(path):
                files.append({
                    'name': filename,
                    'size': os.path.getsize(path),
                    'modified': os.path.getmtime(path)
                })
        
        return jsonify(files)

# Admin Routes
@api_bp.route('/admin/users', methods=['GET'])
@login_required
def admin_list_users():
    if not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Forbidden', 'message': 'Admin access required'}), 403
    users = User.query.all()
    user_list = [
        {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'is_admin': u.is_admin,
            'preferred_language': u.preferred_language,
            'last_login': u.last_login.isoformat() if u.last_login else None,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'is_active': u.is_active
        } for u in users
    ]
    return jsonify({'users': user_list})

# System Routes
@api_bp.route('/system/status')
def system_status():
    return jsonify({
        'status': 'ok',
        'time': datetime.utcnow().isoformat(),
        'users': User.query.count(),
        'conversations': Conversation.query.count(),
        'messages': Message.query.count()
    })

# Test Chatbot Endpoint
@api_bp.route('/test/chat', methods=['POST'])
def test_chat():
    try:
        data = request.get_json()
        question = data.get('question', 'Hello')
        
        # Simple response without any complex processing
        response = {
            'response': f"Test response to: {question}",
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

# Serve static files
@api_bp.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@api_bp.route('/api/document/preview/<filename>', methods=['GET'])
@login_required
def document_preview(filename):
    import mimetypes, os
    docs_folder = current_app.config.get('DOCS_FOLDER', 'docs')
    file_path = os.path.join(docs_folder, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    mime_type, _ = mimetypes.guess_type(file_path)
    return send_file(file_path, mimetype=mime_type or 'application/octet-stream')
