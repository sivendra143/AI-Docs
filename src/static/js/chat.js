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
        this.setupEventListeners();
        this.setupSocket();
        await this.loadUserPreferences();
        await this.loadConversations();
        this.createNewConversation();
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
            
            // If this is a new conversation, update the current conversation ID
            if (data.conversation_id && !this.currentConversationId) {
                this.currentConversationId = data.conversation_id;
                console.log(`[Chat] New conversation started: ${this.currentConversationId}`);
            }
        } else if (data.error) {
            this.addSystemMessage(`Error: ${data.error}`);
        } else {
            console.error('Received malformed response:', data);
            this.addSystemMessage('Received an unexpected response from the server');
        }
        
        if (data.suggestions && data.suggestions.length > 0) {
            this.displaySuggestions(data.suggestions);
        }
        
        console.log('[Chat] Bot response processed:', data);
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
    
    addMessage(text, type) {
        if (!this.chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        if (!this.chatMessages) return;
        
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'message bot';
        typingDiv.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
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
}

// Initialize the chat when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});
