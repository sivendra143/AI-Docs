// chat.js - Main chat functionality

class ChatApp {
    constructor() {
        this.socket = null;
        this.currentConversationId = null;
        this.currentLanguage = 'en';
        this.isProcessing = false;
        
        // DOM Elements
        this.chatMessages = document.getElementById('chat-messages');
        this.questionForm = document.getElementById('question-form');
        this.questionInput = document.getElementById('question-input');
        this.suggestionsContainer = document.getElementById('suggestions-container');
        this.statusIndicator = document.getElementById('status-indicator');
        this.themeSelect = document.getElementById('theme-select');
        this.languageSelect = document.getElementById('language-select');
        this.newChatBtn = document.getElementById('new-chat-btn');
        this.exportTxtBtn = document.getElementById('export-txt-btn');
        this.exportPdfBtn = document.getElementById('export-pdf-btn');
        this.conversationList = document.getElementById('conversation-list');
        this.sidebarToggle = document.getElementById('sidebar-toggle');
        this.sidebar = document.querySelector('.sidebar');
        this.mainContent = document.querySelector('.main-content');
        this.helpBtn = document.getElementById('help-btn');
        this.helpModal = document.getElementById('help-modal');
        this.closeHelpModal = document.getElementById('close-help-modal');
        
        this.initialize();
    }
    
    async initialize() {
        console.log('Initializing Chat App...');
        
        // Add CSS animations directly to the document
        this.injectAnimationStyles();
        
        this.setupEventListeners();
        this.setupSocket();
        this.updateStatus('Connecting...');
        await this.loadUserPreferences();
        await this.loadConversations();
        this.createNewConversation();
    }
    
    injectAnimationStyles() {
        // Create a style element
        const style = document.createElement('style');
        // Define animations for fade-in and bounce
        style.innerHTML = `
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            @keyframes bounce {
                0%, 80%, 100% { transform: translateY(0); }
                40% { transform: translateY(-8px); }
            }
        `;
        // Add the style element to the document head
        document.head.appendChild(style);
    }
    
    setupEventListeners() {
        // Form submission
        this.questionForm.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // New chat
        if (this.newChatBtn) {
            this.newChatBtn.addEventListener('click', () => this.createNewConversation());
        }
        
        // Export buttons
        if (this.exportTxtBtn) {
            this.exportTxtBtn.addEventListener('click', () => this.exportConversation('txt'));
        }
        
        if (this.exportPdfBtn) {
            this.exportPdfBtn.addEventListener('click', () => this.exportConversation('pdf'));
        }
        
        // Language change
        if (this.languageSelect) {
            this.languageSelect.addEventListener('change', (e) => this.changeLanguage(e.target.value));
        }
        
        // Theme toggle
        if (this.themeSelect) {
            this.themeSelect.addEventListener('change', (e) => this.changeTheme(e.target.value));
        }
        
        // Sidebar toggle
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }
        
        // Help modal
        if (this.helpBtn) {
            this.helpBtn.addEventListener('click', () => this.toggleHelpModal(true));
        }
        
        if (this.closeHelpModal) {
            this.closeHelpModal.addEventListener('click', () => this.toggleHelpModal(false));
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }
    
    setupSocket() {
        console.log('[WebSocket] Initializing WebSocket connection...');
        
        // Configuration for WebSocket connection
        const socketConfig = {
            reconnection: true,
            reconnectionAttempts: 10,  // Increased from 5 to 10
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,  // Maximum delay between reconnection attempts
            timeout: 15000,  // Increased from 10000 to 15000
            transports: ['websocket', 'polling'],
            upgrade: true,
            forceNew: true,
            autoConnect: true
        };
        
        // Connect to WebSocket server on port 5000
        this.socket = io('http://localhost:5000', socketConfig);
        
        // Connection established
        this.socket.on('connect', () => {
            console.log('[WebSocket] Successfully connected to server');
            this.updateStatus('Connected');
            this.addSystemMessage('Connected to the chat server');
            
            // If we have a current conversation, rejoin it
            if (this.currentConversationId) {
                console.log(`[WebSocket] Rejoining conversation ${this.currentConversationId}`);
                this.socket.emit('join_conversation', {
                    conversation_id: this.currentConversationId
                });
            }
        });
        
        // Connection lost
        this.socket.on('disconnect', (reason) => {
            console.log(`[WebSocket] Disconnected: ${reason}`);
            this.updateStatus('Disconnected');
            
            if (reason === 'io server disconnect') {
                // The server intentionally disconnected us, try to reconnect
                console.log('[WebSocket] Server disconnected us, attempting to reconnect...');
                this.socket.connect();
            } else {
                this.addSystemMessage('Disconnected from the chat server. Attempting to reconnect...');
            }
        });
        
        // Reconnection events
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`[WebSocket] Reconnection attempt ${attemptNumber}`);
            this.updateStatus(`Reconnecting (${attemptNumber}/${socketConfig.reconnectionAttempts})...`);
        });
        
        this.socket.on('reconnect_failed', () => {
            console.error('[WebSocket] Failed to reconnect after all attempts');
            this.updateStatus('Connection failed');
            this.addSystemMessage('Failed to reconnect to the chat server. Please refresh the page to try again.');
        });
        
        // Handle errors
        this.socket.on('connect_error', (error) => {
            console.error('[WebSocket] Connection error:', error);
            this.updateStatus('Connection error');
            this.addSystemMessage(`Connection error: ${error.message}. Retrying...`);
        });
        
        // Handle chat responses
        this.socket.on('ask_response', (data) => {
            console.log('[WebSocket] Received ask_response:', data);
            this.handleBotResponse(data);
        });
        
        // Handle errors from the server
        this.socket.on('error', (error) => {
            console.error('[WebSocket] Error from server:', error);
            this.addSystemMessage(`Error: ${error.message || 'An unknown error occurred'}`);
        });
    }
    
    updateStatus(status) {
        if (this.statusIndicator) {
            this.statusIndicator.textContent = status;
        }
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        const question = this.questionInput.value.trim();
        if (!question || this.isProcessing) return;
        
        this.isProcessing = true;
        this.questionInput.value = '';
        this.addUserMessage(question);
        this.showTypingIndicator();
        
        try {
            this.socket.emit('ask', {
                question: question,
                conversation_id: this.currentConversationId,
                language: this.currentLanguage
            });
        } catch (error) {
            console.error('Error sending message:', error);
            this.addSystemMessage('Failed to send message');
            this.isProcessing = false;
        }
    }
    
    handleBotResponse(data) {
        this.isProcessing = false;
        this.removeTypingIndicator();
        
        // Handle both 'response' and 'answer' fields for backward compatibility
        const responseText = data.response || data.answer;

        if (responseText) {
            this.addBotMessage(responseText);
        }
    }
    
    showTypingIndicator() {
        if (!this.chatMessages) return;
        
        // Remove existing typing indicator if any
        this.removeTypingIndicator();
        
        // Create with inline styles rather than classes
        const typingDiv = document.createElement('div');
        typingDiv.style.width = '100%';
        typingDiv.style.marginBottom = '1rem';
        typingDiv.style.opacity = '0.8';
        typingDiv.id = 'typing-indicator';
        
        // Detect dark mode
        const isDarkMode = document.documentElement.classList.contains('dark') || 
                          window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // Common variables based on theme
        const baseBgColor = isDarkMode ? '#1e1e1e' : '#f3f4f6';
        const baseTextColor = isDarkMode ? '#e2e2e2' : '#111827';
        const baseBorderColor = isDarkMode ? '#333333' : '#e0e0e0';
        
        typingDiv.innerHTML = `
        <div style="max-width: 85%; margin-right: auto; padding: 1rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
            background-color: ${baseBgColor}; border: 1px solid ${baseBorderColor}; color: ${baseTextColor}; border-bottom-left-radius: 4px;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem; gap: 0.5rem;">
                <span style="width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 50%; 
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; font-size: 1.2rem;">🤖</span>
                <span style="font-weight: 600; font-size: 0.9rem;">PDF Assistant</span>
                <span style="font-size: 0.7rem; background-color: rgba(0,0,0,0.1); padding: 0.1rem 0.3rem; border-radius: 4px;">EN</span>
            </div>
            <div style="word-wrap: break-word;">
                <div style="display: flex; align-items: center; gap: 4px; padding: 6px 0;">
                    <span style="width: 8px; height: 8px; background-color: ${baseTextColor}; border-radius: 50%; opacity: 0.6; display: inline-block; animation: bounce 1.2s infinite 0s;"></span>
                    <span style="width: 8px; height: 8px; background-color: ${baseTextColor}; border-radius: 50%; opacity: 0.6; display: inline-block; animation: bounce 1.2s infinite 0.2s;"></span>
                    <span style="width: 8px; height: 8px; background-color: ${baseTextColor}; border-radius: 50%; opacity: 0.6; display: inline-block; animation: bounce 1.2s infinite 0.4s;"></span>
                </div>
            </div>
        </div>`;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    addMessage(text, type, lang = 'EN') {
        if (!this.chatMessages) return;
        
        // Create message wrapper
        const messageDiv = document.createElement('div');
        messageDiv.style.width = '100%';
        messageDiv.style.marginBottom = '1rem';
        messageDiv.style.animation = 'fadeIn 0.3s ease';
        
        // Detect dark mode
        const isDarkMode = document.documentElement.classList.contains('dark') || 
                          window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // Common variables based on theme
        const baseBgColor = isDarkMode ? '#1e1e1e' : '#f3f4f6';
        const baseTextColor = isDarkMode ? '#e2e2e2' : '#111827';
        const baseBorderColor = isDarkMode ? '#333333' : '#e0e0e0';
        
        let messageHtml = '';
        
        if (type === 'user') {
            messageHtml = `
            <div style="max-width: 85%; margin-left: auto; padding: 1rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
                background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%); color: white; border-bottom-right-radius: 4px;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem; gap: 0.5rem;">
                    <span style="width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 50%; 
                        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; font-size: 1.2rem;">👤</span>
                    <span style="font-weight: 600; font-size: 0.9rem;">You</span>
                    <span style="font-size: 0.7rem; background-color: rgba(0,0,0,0.1); padding: 0.1rem 0.3rem; border-radius: 4px;">${lang}</span>
                </div>
                <div style="word-wrap: break-word;">
                    <p style="margin: 0; line-height: 1.5;">${this.escapeHtml(text)}</p>
                </div>
            </div>`;
        } 
        else if (type === 'bot') {
            messageHtml = `
            <div style="max-width: 85%; margin-right: auto; padding: 1rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
                background-color: ${baseBgColor}; border: 1px solid ${baseBorderColor}; color: ${baseTextColor}; border-bottom-left-radius: 4px;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem; gap: 0.5rem;">
                    <span style="width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 50%; 
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; font-size: 1.2rem;">🤖</span>
                    <span style="font-weight: 600; font-size: 0.9rem;">PDF Assistant</span>
                    <span style="font-size: 0.7rem; background-color: rgba(0,0,0,0.1); padding: 0.1rem 0.3rem; border-radius: 4px;">${lang}</span>
                </div>
                <div style="word-wrap: break-word;">
                    <p style="margin: 0; line-height: 1.5;">${this.escapeHtml(text)}</p>
                    <div style="margin-top: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                        <button class="translate-btn" style="background: linear-gradient(90deg, #6366f1 60%, #43a047 100%); color: #fff; border: none; 
                            border-radius: 0.7em; padding: 0.2em 0.9em; font-size: 0.89em; cursor: pointer; box-shadow: 0 1px 4px rgba(99,102,241,0.2);">Translate</button>
                        <select class="translate-lang" style="border-radius: 0.7em; padding: 0.15em 0.7em; font-size: 0.92em; 
                            border: 1px solid ${baseBorderColor}; background-color: ${baseBgColor}; color: ${baseTextColor};">
                            <option value="en">🇺🇸 English</option>
                            <option value="hi">🇮🇳 Hindi</option>
                            <option value="te">🇮🇳 Telugu</option>
                            <option value="es">🇪🇸 Spanish</option>
                            <option value="fr">🇫🇷 French</option>
                            <option value="de">🇩🇪 German</option>
                            <option value="zh">🇨🇳 Chinese</option>
                            <option value="ja">🇯🇵 Japanese</option>
                            <option value="ru">🇷🇺 Russian</option>
                            <option value="it">🇮🇹 Italian</option>
                            <option value="pt">🇵🇹 Portuguese</option>
                        </select>
                    </div>
                    <div class="translated-text" style="display: none; margin-top: 0.8rem; padding: 0.5rem; 
                        background-color: rgba(0,0,0,0.05); border-radius: 8px; font-style: italic;"></div>
                </div>
            </div>`;
        } 
        else if (type === 'system') {
            const systemBgColor = isDarkMode ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';
            const systemTextColor = isDarkMode ? '#aaaaaa' : '#666666';
            const systemBorderColor = isDarkMode ? '#444444' : '#dddddd';
            
            messageHtml = `
            <div style="max-width: 70%; margin: 0 auto; padding: 0.5rem 1rem; border-radius: 12px; text-align: center; font-size: 0.9rem; 
                background-color: ${systemBgColor}; border: 1px dashed ${systemBorderColor}; color: ${systemTextColor};">
                <div style="word-wrap: break-word;">
                    <p style="margin: 0; line-height: 1.5;">${this.escapeHtml(text)}</p>
                </div>
            </div>`;
        }
        
        messageDiv.innerHTML = messageHtml;
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Add event listener for translate button
        const translateBtn = messageDiv.querySelector('.translate-btn');
        if (translateBtn) {
            translateBtn.addEventListener('click', () => {
                const select = messageDiv.querySelector('.translate-lang');
                const targetLang = select.value;
                this.translateMessage(messageDiv, text, targetLang);
            });
        }
    }

    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }

    async loadUserPreferences() {
        // Implementation depends on your app's preference system
        console.log('Loading user preferences...');
    }

    async loadConversations() {
        // Implementation depends on your app's conversation system
        console.log('Loading conversations...');
    }

    createNewConversation() {
        // Implementation depends on your app's conversation system
        console.log('Creating new conversation...');
    }

    exportConversation(format) {
        // Implementation depends on your app's export functionality
        console.log(`Exporting conversation as ${format}...`);
    }

    changeLanguage(language) {
        // Implementation depends on your app's language system
        console.log(`Changing language to ${language}...`);
    }

    changeTheme(theme) {
        // Implementation depends on your app's theme system
        console.log(`Changing theme to ${theme}...`);
    }

    toggleSidebar() {
        // Implementation depends on your app's UI
        console.log('Toggling sidebar...');
    }

    toggleHelpModal(show) {
        // Implementation depends on your app's help modal
        console.log(`Toggling help modal: ${show}`);
    }

    handleKeyboardShortcuts(e) {
        // Implementation depends on your app's keyboard shortcuts
        console.log('Handling keyboard shortcut...', e.key);
    }

    displaySuggestions(suggestions) {
        // Implementation depends on your app's suggestion system
        console.log('Displaying suggestions:', suggestions);
    }

    addUserMessage(text) {
        this.addMessage(text, 'user');
    }

    addBotMessage(text) {
        this.addMessage(text, 'bot');
    }

    addSystemMessage(text) {
        this.addMessage(text, 'system');
    }
    
    // Method to escape HTML to prevent XSS
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
    
    // Method to handle translation requests
    async translateMessage(messageDiv, text, targetLang) {
        const translatedTextDiv = messageDiv.querySelector('.translated-text');
        if (!translatedTextDiv) return;
        
        translatedTextDiv.textContent = 'Translating...';
        translatedTextDiv.style.display = 'block';
        
        try {
            // In a real app, you would call your translation API here
            // For now, we'll simulate a translation
            await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
            
            // Example translation simulation
            let translatedText;
            if (targetLang === 'hi') {
                translatedText = 'यह एक अनुवादित संदेश है।';
            } else if (targetLang === 'es') {
                translatedText = 'Este es un mensaje traducido.';
            } else if (targetLang === 'fr') {
                translatedText = 'Voici un message traduit.';
            } else {
                translatedText = `Translation to ${targetLang}: ${text}`;
            }
            
            translatedTextDiv.textContent = translatedText;
        } catch (error) {
            console.error('Translation error:', error);
            translatedTextDiv.textContent = 'Translation failed';
        }
    }
}

// Initialize the chat when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});
