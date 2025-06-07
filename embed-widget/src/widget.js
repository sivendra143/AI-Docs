// Widget initialization
class PDFChatWidget {
    constructor(config = {}) {
        this.config = {
            apiUrl: config.apiUrl || window.location.origin,
            position: config.position || 'bottom-right',
            primaryColor: config.primaryColor || '#4f46e5',
            title: config.title || 'PDF Chat Assistant',
            ...config
        };
        this.isOpen = false;
        this.initialize();
    }

    initialize() {
        this.createWidget();
        this.setupEventListeners();
    }

    createWidget() {
        // Create container
        this.widget = document.createElement('div');
        this.widget.className = 'pdf-chat-widget';
        // Add debug style
        this.widget.style.border = '2px solid red'; // Debug border
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
                ${this.getPositionStyles()};
                z-index: 9999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            .widget-toggle {
                position: absolute;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: ${this.config.primaryColor};
                color: white;
                border: none;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }
            .widget-toggle:hover {
                transform: scale(1.05);
                box-shadow: 0 6px 16px rgba(0,0,0,0.2);
            }
            .widget-container {
                position: absolute;
                bottom: 70px;
                right: 0;
                width: 350px;
                max-width: 90vw;
                height: 500px;
                max-height: 80vh;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                transform: translateY(20px);
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
            }
            .widget-container.visible {
                transform: translateY(0);
                opacity: 1;
                visibility: visible;
            }
            .widget-header {
                padding: 16px;
                background: ${this.config.primaryColor};
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
                padding: 0;
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
                padding: 12px;
                border-top: 1px solid #eee;
                display: flex;
                gap: 8px;
            }
            .chat-input {
                flex: 1;
                padding: 10px 12px;
                border: 1px solid #ddd;
                border-radius: 20px;
                outline: none;
            }
            .send-button {
                padding: 0 16px;
                background: ${this.config.primaryColor};
                color: white;
                border: none;
                border-radius: 20px;
                cursor: pointer;
                transition: background 0.2s;
            }
            .send-button:hover {
                background: ${this.darkenColor(this.config.primaryColor, 10)};
            }
            .message {
                margin-bottom: 12px;
                max-width: 80%;
                padding: 8px 12px;
                border-radius: 16px;
                line-height: 1.4;
            }
            .user {
                margin-left: auto;
                background: ${this.config.primaryColor};
                color: white;
                border-bottom-right-radius: 4px;
            }
            .bot {
                margin-right: auto;
                background: #f0f0f0;
                color: #333;
                border-bottom-left-radius: 4px;
            }
        `;
        document.head.appendChild(style);
    }

    getPositionStyles() {
        const positions = {
            'top-left': 'top: 20px; left: 20px;',
            'top-right': 'top: 20px; right: 20px;',
            'bottom-left': 'bottom: 20px; left: 20px;',
            'bottom-right': 'bottom: 20px; right: 20px;',
        };
        return positions[this.config.position] || positions['bottom-right'];
    }

    darkenColor(color, percent) {
        // Simple color darkening function
        const num = parseInt(color.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) - amt;
        const G = (num >> 8 & 0x00FF) - amt;
        const B = (num & 0x0000FF) - amt;
        return '#' + (0x1000000 + (R < 0 ? 0 : R) * 0x10000 +
            (G < 0 ? 0 : G) * 0x100 + (B < 0 ? 0 : B)).toString(16).slice(1);
    }

    setupEventListeners() {
        const toggleBtn = this.widget.querySelector('.widget-toggle');
        const closeBtn = this.widget.querySelector('.widget-close');
        const sendBtn = this.widget.querySelector('.send-button');
        const input = this.widget.querySelector('.chat-input');
        
        toggleBtn.addEventListener('click', () => this.toggleWidget());
        closeBtn.addEventListener('click', () => this.toggleWidget(false));
        sendBtn.addEventListener('click', () => this.sendMessage(input));
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage(input);
        });
    }

    toggleWidget(show = !this.isOpen) {
        this.isOpen = show;
        const container = this.widget.querySelector('.widget-container');
        if (show) {
            container.classList.add('visible');
        } else {
            container.classList.remove('visible');
        }
    }

    async sendMessage(input) {
        const message = input.value.trim();
        if (!message) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        input.value = '';

        try {
            // Show typing indicator
            this.addMessage('...', 'bot typing');

            // Send to your API
            const response = await fetch(`${this.config.apiUrl}/api/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message })
            });

            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator();
            
            // Add bot response
            if (data.answer) {
                this.addMessage(data.answer, 'bot');
            } else {
                this.addMessage('Sorry, I encountered an error.', 'bot');
            }
        } catch (error) {
            this.removeTypingIndicator();
            this.addMessage('Error connecting to the server.', 'bot');
            console.error('Error:', error);
        }
    }

    addMessage(text, type = 'user') {
        if (type === 'bot typing') {
            const typing = document.createElement('div');
            typing.className = 'message bot typing';
            typing.textContent = text;
            this.widget.querySelector('.chat-messages').appendChild(typing);
            this.scrollToBottom();
            return typing;
        }
        
        const message = document.createElement('div');
        message.className = `message ${type}`;
        message.textContent = text;
        this.widget.querySelector('.chat-messages').appendChild(message);
        this.scrollToBottom();
        return message;
    }

    removeTypingIndicator() {
        const typing = this.widget.querySelector('.typing');
        if (typing) {
            typing.remove();
        }
    }

    scrollToBottom() {
        const messages = this.widget.querySelector('.chat-messages');
        messages.scrollTop = messages.scrollHeight;
    }
}

// Export the widget class
if (typeof module !== 'undefined' && module.exports) {
    // For Node.js/CommonJS
    module.exports = PDFChatWidget;
} else if (typeof define === 'function' && define.amd) {
    // For AMD/RequireJS
    define([], function() { return PDFChatWidget; });
} else {
    // For browser globals
    window.PDFChatWidget = PDFChatWidget;
}
