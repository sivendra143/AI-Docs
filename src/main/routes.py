from flask import Blueprint, render_template, jsonify, request
from src.services.chat_service import get_chat_response

main_bp = Blueprint('main', __name__)

from flask_login import current_user

@main_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('login.html')
    return render_template('index.html')

@main_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
            
        question = data['question'].strip()
        if not question:
            return jsonify({'error': 'Empty question'}), 400
            
        # Get response from chat service
        response = get_chat_response(question)
        
        return jsonify({
            'response': response,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@main_bp.route('/test')
def test():
    return jsonify({'status': 'ok', 'message': 'Flask is running!'})
