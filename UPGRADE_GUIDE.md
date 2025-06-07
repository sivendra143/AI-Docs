# Upgrade Guide

This document provides detailed instructions for implementing the future upgrades planned for the PDF Chatbot.

## Table of Contents

1. [Adding Support for Additional File Types](#adding-support-for-additional-file-types)
2. [Implementing Whisper-based Voice Input](#implementing-whisper-based-voice-input)
3. [Setting Up WebSocket/REST API Endpoints](#setting-up-websocketrest-api-endpoints)
4. [Implementing User Authentication](#implementing-user-authentication)
5. [Adding Dark/Light Theme Toggle](#adding-darklight-theme-toggle)
6. [Enabling Admin Analytics](#enabling-admin-analytics)

## Adding Support for Additional File Types

The chatbot already includes a `document_processor.py` module that supports multiple file types. To fully implement or extend this functionality:

### Step 1: Install Required Dependencies

```bash
pip install python-docx pandas
```

### Step 2: Update Configuration

Add file type settings to `config.json`:

```json
{
    "supported_file_types": ["pdf", "docx", "txt", "csv"],
    "docs_folder": "./docs/"
}
```

### Step 3: Update Application Code

Modify the main application to use `DocumentProcessor` instead of `PDFProcessor`:

```python
from document_processor import DocumentProcessor

# Initialize with the docs folder
processor = DocumentProcessor(config['docs_folder'])
processor.process_documents()
```

### Step 4: Add UI Elements

Update the web interface to show supported file types:

```html
<div class="supported-formats">
    <p>Supported formats: PDF, DOCX, TXT, CSV</p>
</div>
```

## Implementing Whisper-based Voice Input

### Step 1: Install Whisper

```bash
pip install openai-whisper
```

### Step 2: Add Audio Recording to Web UI

Add these elements to `index.html`:

```html
<div class="voice-input-container">
    <button id="start-recording" class="voice-btn">
        <span class="mic-icon">🎤</span> Start Recording
    </button>
    <button id="stop-recording" class="voice-btn" disabled>
        <span class="stop-icon">⏹️</span> Stop Recording
    </button>
    <div id="recording-status"></div>
</div>
```

### Step 3: Add JavaScript for Audio Recording

Create `voice.js` in the static/js folder:

```javascript
let mediaRecorder;
let audioChunks = [];

document.getElementById('start-recording').addEventListener('click', startRecording);
document.getElementById('stop-recording').addEventListener('click', stopRecording);

async function startRecording() {
    audioChunks = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    
    mediaRecorder.addEventListener('dataavailable', event => {
        audioChunks.push(event.data);
    });
    
    mediaRecorder.start();
    
    document.getElementById('start-recording').disabled = true;
    document.getElementById('stop-recording').disabled = false;
    document.getElementById('recording-status').textContent = 'Recording...';
}

async function stopRecording() {
    mediaRecorder.stop();
    
    document.getElementById('start-recording').disabled = false;
    document.getElementById('stop-recording').disabled = true;
    document.getElementById('recording-status').textContent = 'Processing...';
    
    // Wait for the dataavailable event to finish
    await new Promise(resolve => {
        mediaRecorder.addEventListener('stop', resolve);
    });
    
    // Create audio blob and send to server
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio', audioBlob);
    
    try {
        const response = await fetch('/api/voice', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Add user message with transcription
        addUserMessage(data.transcription);
        
        // Add bot response
        addBotMessage(data.answer);
        
        // Display suggestions
        displaySuggestions(data.suggestions);
        
        document.getElementById('recording-status').textContent = '';
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('recording-status').textContent = 'Error processing audio';
    }
}
```

### Step 4: Connect Voice Processing in App

Update `app.py` to include voice routes:

```python
from voice_input import setup_voice_routes

# After initializing the app and chatbot
setup_voice_routes(app, chatbot)
```

## Setting Up WebSocket/REST API Endpoints

### Step 1: Install Dependencies

```bash
pip install flask-socketio pyjwt
```

### Step 2: Set Up API Routes

The `api.py` module already includes REST API endpoints. To fully implement:

1. Import and register the API blueprint in `app.py`:

```python
from api import setup_api_routes

# After initializing the app and chatbot
setup_api_routes(app, chatbot)
```

### Step 3: Add WebSocket Support

Create a new file `websocket.py`:

```python
from flask_socketio import SocketIO, emit
import functools

def setup_websocket(app, chatbot):
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    def authenticated_only(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if not request.args.get('token'):
                disconnect()
                return
            try:
                token = request.args.get('token')
                # Verify token here
                return f(*args, **kwargs)
            except:
                disconnect()
        return wrapped
    
    @socketio.on('connect')
    def handle_connect():
        emit('connected', {'status': 'connected'})
    
    @socketio.on('ask')
    @authenticated_only
    def handle_ask(data):
        question = data.get('question', '')
        if not question:
            emit('answer', {
                'answer': "Please ask a question.",
                'suggestions': []
            })
            return
        
        answer = chatbot.ask_question(question)
        suggestions = chatbot.get_smart_suggestions(question, answer)
        
        emit('answer', {
            'answer': answer,
            'suggestions': suggestions
        })
    
    return socketio
```

Then update `app.py`:

```python
from websocket import setup_websocket

# After initializing the app and chatbot
socketio = setup_websocket(app, chatbot)

# Replace app.run with socketio.run
if __name__ == '__main__':
    initialize_app()
    socketio.run(app, host=config['host'], port=config['port'], debug=True)
```

## Implementing User Authentication

### Step 1: Create Login Page

Create `login.html` in the templates folder:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - PDF Chatbot</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/login.css') }}">
</head>
<body>
    <div class="login-container">
        <div class="login-card">
            <h1>PDF Chatbot</h1>
            <h2>Login</h2>
            <form id="login-form">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <div class="error-message" id="login-error"></div>
                <button type="submit" class="login-btn">Login</button>
            </form>
        </div>
    </div>
    
    <script>
        document.getElementById('login-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorElement = document.getElementById('login-error');
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Store token and redirect
                    localStorage.setItem('auth_token', data.token);
                    window.location.href = '/';
                } else {
                    errorElement.textContent = data.message || 'Login failed';
                }
            } catch (error) {
                console.error('Error:', error);
                errorElement.textContent = 'An error occurred. Please try again.';
            }
        });
    </script>
</body>
</html>
```

### Step 2: Add Authentication Check to Main App

Update `app.py` to include authentication routes:

```python
@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/')
def index():
    # For public access without authentication
    return render_template('index.html')

@app.route('/protected')
def protected_page():
    # For protected pages
    return render_template('protected.html')
```

### Step 3: Update JavaScript to Include Authentication

Add authentication handling to `script.js`:

```javascript
// Check if token exists
const token = localStorage.getItem('auth_token');
const isProtectedPage = document.body.classList.contains('protected-page');

if (isProtectedPage && !token) {
    window.location.href = '/login';
}

// Add token to API requests
async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
        if (isProtectedPage) {
            window.location.href = '/login';
            return;
        }
    } else {
        if (!options.headers) options.headers = {};
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    return fetch(url, options);
}

// Use fetchWithAuth for API calls
async function askQuestion(question) {
    try {
        const response = await fetchWithAuth('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });
        
        if (response.status === 401) {
            localStorage.removeItem('auth_token');
            if (isProtectedPage) {
                window.location.href = '/login';
                return;
            }
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}
```

## Adding Dark/Light Theme Toggle

The theme toggle functionality is already implemented in `theme.js`. To fully implement:

### Step 1: Add CSS Variables for Both Themes

This is already done in `styles.css`.

### Step 2: Add Theme Toggle Button to All Pages

Ensure the theme toggle button is included in all page templates:

```html
<div class="theme-toggle">
    <button id="theme-toggle-btn">
        <span class="light-icon">☀️</span>
        <span class="dark-icon">🌙</span>
    </button>
</div>
```

### Step 3: Include Theme Script in All Pages

Add to all HTML templates:

```html
<script src="{{ url_for('static', filename='js/theme.js') }}"></script>
```

## Enabling Admin Analytics

### Step 1: Create Admin Dashboard Page

Create `admin.html` in the templates folder:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - PDF Chatbot</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/admin.css') }}">
</head>
<body class="protected-page">
    <div class="app-container" id="admin-panel">
        <header>
            <h1>PDF Chatbot Admin</h1>
            <div class="theme-toggle">
                <button id="theme-toggle-btn">
                    <span class="light-icon">☀️</span>
                    <span class="dark-icon">🌙</span>
                </button>
            </div>
        </header>

        <main>
            <div class="admin-controls">
                <button id="refresh-analytics" class="action-btn">Refresh Data</button>
                <a href="/" class="action-btn">Back to Chat</a>
            </div>
            
            <div id="loading-indicator" class="loading">Loading analytics data...</div>
            
            <div id="analytics-data" class="analytics-container">
                <!-- Analytics data will be loaded here -->
            </div>
        </main>

        <footer>
            <div class="info">
                <p>PDF Chatbot Admin | <span id="status-indicator">Ready</span></p>
            </div>
        </footer>
    </div>

    <script src="{{ url_for('static', filename='js/theme.js') }}"></script>
    <script src="{{ url_for('static', filename='js/analytics.js') }}"></script>
</body>
</html>
```

### Step 2: Add Admin Route to App

Update `app.py`:

```python
@app.route('/admin')
def admin_page():
    return render_template('admin.html')
```

### Step 3: Add Admin CSS

Create `admin.css` in the static/css folder:

```css
.analytics-container {
    padding: 1rem;
}

.analytics-summary {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
}

.analytics-card {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 1rem;
    flex: 1;
    text-align: center;
}

.analytics-number {
    font-size: 2rem;
    font-weight: 600;
    color: var(--primary-color);
}

.analytics-section {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
}

.analytics-section h3 {
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
}

.top-queries-list {
    list-style: none;
    padding: 0;
}

.top-queries-list li {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-color);
}

.query-count {
    font-weight: 600;
    color: var(--primary-color);
}

.recent-queries-table {
    width: 100%;
    border-collapse: collapse;
}

.recent-queries-table th,
.recent-queries-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

.recent-queries-table th {
    font-weight: 600;
    background-color: var(--bg-color);
}

.status {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 600;
}

.status.success {
    background-color: var(--success-color);
    color: white;
}

.status.failure {
    background-color: var(--error-color);
    color: white;
}

.admin-controls {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.loading {
    text-align: center;
    padding: 2rem;
    color: var(--text-light);
}

.error-message {
    background-color: var(--error-color);
    color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}
```

## Conclusion

This upgrade guide provides detailed instructions for implementing all the planned future features. Each section includes the necessary code and configuration changes to enable the functionality.

To implement any of these upgrades:

1. Follow the step-by-step instructions in the relevant section
2. Test each feature thoroughly before deploying to production
3. Update the documentation to reflect the new capabilities

For any questions or issues, please refer to the project repository or contact the maintainers.

