from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

# Import your PDF processing modules
from llm_rag import ChatbotLLM
from document_processor import DocumentProcessor

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for all routes

# Initialize the chatbot
print("Initializing chatbot...")
try:
    # Initialize document processor and load PDFs
    doc_processor = DocumentProcessor()
    
    # Process PDFs from the uploads directory
    uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    if os.path.exists(uploads_dir) and os.path.isdir(uploads_dir):
        pdf_files = [f for f in os.listdir(uploads_dir) if f.lower().endswith('.pdf')]
        for pdf_file in pdf_files:
            file_path = os.path.join(uploads_dir, pdf_file)
            print(f"Processing PDF: {file_path}")
            doc_processor.process_document(file_path)
    
    # Initialize the chatbot with the vector store
    chatbot = ChatbotLLM(doc_processor.vector_store)
    print("Chatbot initialized successfully!")
except Exception as e:
    print(f"Error initializing chatbot: {str(e)}")
    chatbot = None

# Simple in-memory storage for chat messages
chat_history = []

@app.route('/', methods=['GET'])
def serve_index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple Chat</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }
            #chat { border: 1px solid #ccc; padding: 20px; border-radius: 5px; }
            #messages { height: 400px; overflow-y: auto; border: 1px solid #ddd; margin-bottom: 10px; padding: 10px; }
            #messageInput { width: 70%; padding: 10px; margin-right: 10px; }
            button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #45a049; }
            .message { margin: 5px 0; padding: 8px; border-radius: 4px; }
            .user { background: #e6f7ff; }
            .bot { background: #f0f0f0; }
        </style>
    </head>
    <body>
        <h1>Simple Chat</h1>
        <div id="chat">
            <div id="messages"></div>
            <div>
                <input type="text" id="messageInput" placeholder="Type a message..." />
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            const messagesDiv = document.getElementById('messages');
            const input = document.getElementById('messageInput');
            
            function addMessage(sender, text) {
                const msg = document.createElement('div');
                msg.className = `message ${sender}`;
                msg.textContent = `${sender}: ${text}`;
                messagesDiv.appendChild(msg);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            async function sendMessage() {
                const message = input.value.trim();
                if (!message) return;
                
                // Add user message
                addMessage('user', message);
                input.value = '';
                
                try {
                    // Show typing indicator
                    const typingId = 'typing' + Date.now();
                    const typingMsg = document.createElement('div');
                    typingMsg.id = typingId;
                    typingMsg.className = 'message bot';
                    typingMsg.textContent = 'Bot: Thinking...';
                    messagesDiv.appendChild(typingMsg);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    
                    // Send to our own backend
                    const response = await fetch('/ask', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ question: message })
                    });
                    
                    // Remove typing indicator
                    messagesDiv.removeChild(typingMsg);
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    addMessage('bot', data.answer || 'No response');
                } catch (error) {
                    console.error('Error:', error);
                    addMessage('bot', `Error: ${error.message}`);
                }
            }
            
            // Allow sending with Enter key
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
            
            // Initial message
            window.onload = () => {
                addMessage('bot', 'Hello! How can I help you today?');
                input.focus();
            };
        </script>
    </body>
    </html>
    """

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        question = data.get('question', '')
        print(f"Received question: {question}")
        
        # Use the chatbot to get a response
        if chatbot is None:
            answer = "Error: Chatbot is not properly initialized. Please check the server logs."
        else:
            try:
                # Get answer from the chatbot
                result = chatbot.qa_chain.invoke({"query": question})
                answer = result.get('result', 'I could not process your question.')
                
                # If the answer is too short or seems like an error, provide a fallback
                if not answer or len(answer) < 5:
                    answer = "I'm not sure how to answer that. Could you provide more details or ask a different question?"
                    
            except Exception as e:
                print(f"Error getting response from chatbot: {str(e)}")
                answer = "I encountered an error while processing your question. Please try again later."
        
        return jsonify({
            'answer': answer,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    print("Starting server on http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    app.run(host='0.0.0.0', port=8000, debug=True)
