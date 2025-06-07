class PDFChatWidget {
    constructor(options = {}) {
        this.config = {
            apiUrl: options.apiUrl || window.location.origin,
            position: options.position || 'bottom-right',
            primaryColor: options.primaryColor || '#4f46e5',
            title: options.title || 'PDF Chat Assistant',
            ...options
        };
        this.isOpen = false;
        this.initialize();
    }

    initialize() {
        this.createWidget();
        this.setupEventListeners();
    }

    createWidget() {
        // Create main widget container
        this.widget = document.createElement('div');
        this.widget.className = 'pdf-chat-widget';
        this.widget.style.border = '2px solid red'; // Make it visible for debugging
        
        // Widget HTML
        this.widget.innerHTML = `
            <div class="widget-container">
                <div class="widget-header">
                    <h3>${this.config.title}</h3>
                    <button class="widget-close">×</button>
                </div>
                <div class="widget-body">
                    <div class="chat-messages"></div>
                    <div class="chat-input-container">
                        <input type="text" class="chat-input" placeholder="Type your question...">
                        <button class="send-button">Send</button>
                    </div>
                </div>
            </div>
            <button class="widget-toggle">
                <svg viewBox="0 0 24 24" width="24" height="24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/>
                </svg>
            </button>
        `;

        // Add to body
        document.body.appendChild(this.widget);
        this.addStyles();
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .pdf-chat-widget {
                position: fixed;
                ${this.getPositionStyles()}
                z-index: 9999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                --primary-color: ${this.config.primaryColor};
            }
            .widget-container {
                position: absolute;
                bottom: 60px;
                right: 0;
                width: 350px;
                max-width: 100%;
                height: 500px;
                max-height: 80vh;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                transform: translateY(20px);
                opacity: 0;
                transition: all 0.3s ease;
            }
            .widget-container.visible {
                transform: translateY(0);
                opacity: 1;
            }
            .widget-header {
                padding: 16px;
                background: var(--primary-color);
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .widget-header h3 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }
            .widget-close {
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                line-height: 1;
                padding: 0 8px;
            }
            .widget-body {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .chat-messages {
                flex: 1;
                padding: 16px;
                overflow-y: auto;
            }
            .chat-input-container {
                padding: 12px 16px;
                border-top: 1px solid #eee;
                display: flex;
                gap: 8px;
            }
            .chat-input {
                flex: 1;
                padding: 10px 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            .send-button {
                background: var(--primary-color);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                cursor: pointer;
                font-weight: 500;
                transition: background 0.2s;
            }
            .send-button:hover {
                opacity: 0.9;
            }
            .widget-toggle {
                position: absolute;
                bottom: 0;
                right: 0;
                width: 56px;
                height: 56px;
                border-radius: 50%;
                background: var(--primary-color);
                border: none;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                transition: all 0.2s;
            }
            .widget-toggle:hover {
                transform: scale(1.05);
            }
            .widget-toggle svg {
                width: 24px;
                height: 24px;
                fill: currentColor;
            }
        `;
        document.head.appendChild(style);
    }

    getPositionStyles() {
        const positions = {
            'top-left': 'top: 20px; left: 20px;',
            'top-right': 'top: 20px; right: 20px;',
            'bottom-left': 'bottom: 20px; left: 20px;',
            'bottom-right': 'bottom: 20px; right: 20px;'
        };
        return positions[this.config.position] || positions['bottom-right'];
    }

    setupEventListeners() {
        // Toggle widget
        const toggleBtn = this.widget.querySelector('.widget-toggle');
        const closeBtn = this.widget.querySelector('.widget-close');
        const container = this.widget.querySelector('.widget-container');
        
        toggleBtn.addEventListener('click', () => {
            this.isOpen = !this.isOpen;
            if (this.isOpen) {
                container.classList.add('visible');
                this.widget.querySelector('.chat-input').focus();
            } else {
                container.classList.remove('visible');
            }
        });

        closeBtn.addEventListener('click', () => {
            this.isOpen = false;
            container.classList.remove('visible');
        });

        // Send message
        const sendBtn = this.widget.querySelector('.send-button');
        const chatInput = this.widget.querySelector('.chat-input');
        
        const sendMessage = () => {
            const message = chatInput.value.trim();
            if (!message) return;

            // Add user message
            this.addMessage('user', message);
            chatInput.value = '';

            // Show typing indicator
            const typingId = this.showTypingIndicator();

            // Send to API
            fetch(`${this.config.apiUrl}/api/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message })
            })
            .then(response => response.json())
            .then(data => {
                // Remove typing indicator
                this.removeTypingIndicator(typingId);
                
                // Add bot response
                if (data.answer) {
                    this.addMessage('bot', data.answer);
                } else {
                    this.addMessage('bot', 'Sorry, I could not process your request.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.removeTypingIndicator(typingId);
                this.addMessage('bot', 'An error occurred while processing your request.');
            });
        };

        sendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    addMessage(sender, text) {
        const messagesContainer = this.widget.querySelector('.chat-messages');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;
        messageElement.textContent = text;
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const typingElement = document.createElement('div');
        typingElement.id = id;
        typingElement.className = 'message bot typing';
        typingElement.textContent = '...';
        this.widget.querySelector('.chat-messages').appendChild(typingElement);
        return id;
    }

    removeTypingIndicator(id) {
        const element = document.getElementById(id);
        if (element) {
            element.remove();
        }
    }
}

// Expose to window
if (typeof window !== 'undefined') {
    window.PDFChatWidget = PDFChatWidget;
}

// For CommonJS/Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PDFChatWidget;
}

// For AMD/RequireJS
if (typeof define === 'function' && define.amd) {
    define('PDFChatWidget', [], function() { return PDFChatWidget; });
}
