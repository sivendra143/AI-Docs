// chat-fixed.js - Clean implementation of the chat functionality with WebSocket support
// Created to resolve all syntax errors and initialization issues

/**
 * ChatApp - Main chat application class
 * Handles WebSocket communication, UI updates, and user interactions
 */
class ChatApp {
    constructor() {
        // Initialize properties
        this.socket = null;
        this.currentConversationId = `conv_${Date.now()}`;
        this.isTyping = false;
        this.debugEnabled = true;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        
        // DOM Elements
        this.chatMessages = document.getElementById('chat-messages');
        this.questionForm = document.getElementById('question-form');
        this.questionInput = document.getElementById('question-input');
        this.suggestionsContainer = document.getElementById('suggestions-container');
        this.statusIndicator = document.getElementById('status-indicator');
        
        console.log('ChatApp initializing...');
        
        // Initialize WebSocket
        this.initializeWebSocket();
        
        // Set up event listeners
        if (this.questionForm) {
            this.questionForm.addEventListener('submit', this.handleSubmit.bind(this));
        } else {
            console.warn('Question form not found in the DOM');
        }
        
        console.log('ChatApp initialized');
    }
    
    /**
     * Initialize WebSocket connection
     */
    initializeWebSocket() {
        console.log('Initializing WebSocket connection...');
        
        // If socket already exists, disconnect it first
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        
        // Check if Socket.IO is available
        if (typeof io === 'undefined') {
            console.error('Socket.IO client not loaded');
            this.addSystemMessage('Error: Chat features not available. Socket.IO client not loaded.', 'error');
            return;
        }
        
        try {
            // Configure socket options
            const socketOptions = {
                reconnection: true,
                reconnectionAttempts: this.maxReconnectAttempts,
                reconnectionDelay: this.reconnectDelay,
                reconnectionDelayMax: 10000, // 10 seconds max delay
                timeout: 20000,
                autoConnect: true,
                transports: ['websocket', 'polling'], // Prioritize WebSocket
                upgrade: true,
                forceNew: true,
                withCredentials: true,
                path: '/socket.io',
                secure: window.location.protocol === 'https:'
            };
            
            // Initialize socket
            this.socket = io(socketOptions);
            
            // Store socket instance globally for debugging
            window.chatSocket = this.socket;
            
            // Setup socket event handlers
            this.setupSocketEventHandlers();
            
            // Update UI to show connecting status
            this.updateConnectionStatus('connecting');
            
            console.log('WebSocket initialization complete');
        } catch (error) {
            console.error('Error initializing WebSocket:', error);
            this.addSystemMessage('Error connecting to chat server. Please try again later.', 'error');
            this.updateConnectionStatus(false);
        }
    }
    
    /**
     * Set up socket event handlers
     */
    setupSocketEventHandlers() {
        if (!this.socket) return;
        
        // Connection established
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
            this.addSystemMessage('Connected to chat server', 'success');
            
            // Join conversation room
            this.socket.emit('join_conversation', { 
                conversation_id: this.currentConversationId 
            });
        });
        
        // Connection lost
        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket disconnected:', reason);
            this.updateConnectionStatus(false);
            this.addSystemMessage('Disconnected from chat server', 'warning');
        });
        
        // Connection error
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.updateConnectionStatus(false);
            this.addSystemMessage('Error connecting to chat server', 'error');
        });
        
        // Handle incoming messages
        this.socket.on('message', (data) => {
            this.handleIncomingMessage(data);
        });
        
        // Handle new messages
        this.socket.on('new_message', (data) => {
            this.handleIncomingMessage(data);
        });
        
        // Handle typing indicator
        this.socket.on('typing', (data) => {
            if (data.conversation_id === this.currentConversationId) {
                this.showTypingIndicator();
            }
        });
        
        // Handle stop typing
        this.socket.on('stop_typing', (data) => {
            if (data.conversation_id === this.currentConversationId) {
                this.removeTypingIndicator();
            }
        });
        
        // Handle message received acknowledgement
        this.socket.on('message_received', (data) => {
            console.log('Message received by server:', data);
        });
        
        // Handle errors
        this.socket.on('error', (data) => {
            console.error('WebSocket error:', data);
            this.addSystemMessage('Error: ' + (data.message || 'Unknown error'), 'error');
        });
    }
    
    /**
     * Handle form submission
     * @param {Event} event - Form submit event
     */
    handleSubmit(event) {
        if (event) event.preventDefault();
        
        const message = this.questionInput.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.addUserMessage(message);
        
        // Clear input
        this.questionInput.value = '';
        
        // Send message to server via WebSocket
        if (this.socket && this.socket.connected) {
            this.socket.emit('new_message', {
                message: message,
                conversation_id: this.currentConversationId,
                timestamp: new Date().toISOString()
            });
        } else {
            console.error('Socket not connected');
            this.addSystemMessage('Not connected to chat server. Please try again later.', 'error');
            
            // Attempt to reconnect
            this.initializeWebSocket();
        }
    }
    
    /**
     * Handle incoming WebSocket messages
     * @param {Object} data - The message data
     */
    handleIncomingMessage(data) {
        try {
            console.log('Received message:', data);
            
            // Skip if message doesn't belong to current conversation
            if (data.conversation_id && data.conversation_id !== this.currentConversationId) {
                console.log('Message belongs to different conversation, skipping');
                return;
            }
            
            // Handle different message types
            switch (data.type) {
                case 'new_message':
                    // Add bot message to chat
                    this.addBotMessage(data.message, data.timestamp);
                    
                    // Show suggestions if provided
                    if (data.suggestions && Array.isArray(data.suggestions)) {
                        this.showSuggestions(data.suggestions);
                    }
                    break;
                    
                case 'typing':
                    this.showTypingIndicator();
                    break;
                    
                case 'stop_typing':
                    this.removeTypingIndicator();
                    break;
                    
                case 'message_received':
                    // Confirmation that server received message
                    console.log('Server received message:', data);
                    break;
                    
                case 'error':
                    this.addSystemMessage('Error: ' + (data.message || 'Unknown error'), 'error');
                    break;
                    
                default:
                    // Default to adding a bot message if type not specified
                    if (data.message) {
                        this.addBotMessage(data.message, data.timestamp);
                    }
            }
            
            // Handle conversation ID updates
            if (data.conversation_id && data.conversation_id !== this.currentConversationId) {
                console.log('Updating conversation ID:', data.conversation_id);
                this.currentConversationId = data.conversation_id;
            }
            
            // Scroll to bottom to show new messages
            this.scrollToBottom();
            
        } catch (error) {
            console.error('Error handling incoming message:', error, data);
            this.addSystemMessage('Error processing message', 'error');
        }
    }
    
    /**
     * Add a user message to the chat
     * @param {string} message - The message text
     * @param {string} [timestamp] - Optional timestamp
     */
    addUserMessage(message, timestamp = new Date().toISOString()) {
        if (!message) return;
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'user');
        
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${this.escapeHtml(message)}</p>
                <span class="timestamp">${new Date(timestamp).toLocaleTimeString()}</span>
            </div>
        `;
        
        if (this.chatMessages) {
            this.chatMessages.appendChild(messageElement);
            this.scrollToBottom();
        }
    }
    
    /**
     * Add a bot message to the chat
     * @param {string} message - The message text
     * @param {string} [timestamp] - Optional timestamp
     */
    addBotMessage(message, timestamp = new Date().toISOString()) {
        if (!message) return;
        
        // Remove typing indicator if present
        this.removeTypingIndicator();
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'bot');
        
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${this.escapeHtml(message)}</p>
                <span class="timestamp">${new Date(timestamp).toLocaleTimeString()}</span>
            </div>
        `;
        
        if (this.chatMessages) {
            this.chatMessages.appendChild(messageElement);
            this.scrollToBottom();
        }
    }
    
    /**
     * Add a system message to the chat
     * @param {string} message - The message text
     * @param {string} [severity='info'] - Message severity (info, success, warning, error)
     * @param {string} [timestamp] - Optional timestamp
     */
    addSystemMessage(message, severity = 'info', timestamp = new Date().toISOString()) {
        if (!message) return;
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'system', severity);
        
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${this.escapeHtml(message)}</p>
                <span class="timestamp">${new Date(timestamp).toLocaleTimeString()}</span>
            </div>
        `;
        
        if (this.chatMessages) {
            this.chatMessages.appendChild(messageElement);
            this.scrollToBottom();
        }
    }
    
    /**
     * Show typing indicator in the chat
     */
    showTypingIndicator() {
        // Remove existing typing indicator if any
        this.removeTypingIndicator();
        
        const typingElement = document.createElement('div');
        typingElement.id = 'typing-indicator';
        typingElement.classList.add('message', 'bot', 'typing');
        
        typingElement.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        if (this.chatMessages) {
            this.chatMessages.appendChild(typingElement);
            this.scrollToBottom();
        }
    }
    
    /**
     * Remove typing indicator from the chat
     */
    removeTypingIndicator() {
        const typingElement = document.getElementById('typing-indicator');
        if (typingElement && typingElement.parentNode) {
            typingElement.parentNode.removeChild(typingElement);
        }
    }
    
    /**
     * Show clickable suggestions below a message
     * @param {Array} suggestions - Array of suggestion strings
     */
    showSuggestions(suggestions) {
        if (!Array.isArray(suggestions) || suggestions.length === 0) return;
        
        const suggestionsContainer = this.suggestionsContainer;
        if (!suggestionsContainer) return;
        
        // Clear existing suggestions
        suggestionsContainer.innerHTML = '';
        
        // Create and append new suggestions
        suggestions.forEach(suggestion => {
            const suggestionElement = document.createElement('button');
            suggestionElement.classList.add('suggestion');
            suggestionElement.textContent = suggestion;
            
            // Add click event to send this suggestion as a message
            suggestionElement.addEventListener('click', () => {
                this.questionInput.value = suggestion;
                this.handleSubmit();
                
                // Clear suggestions after selecting one
                suggestionsContainer.innerHTML = '';
            });
            
            suggestionsContainer.appendChild(suggestionElement);
        });
        
        // Make suggestions container visible
        suggestionsContainer.style.display = 'flex';
    }
    
    /**
     * Update the connection status in the UI
     * @param {boolean|string} status - Connection status (true, false, or 'connecting')
     */
    updateConnectionStatus(status) {
        let statusText, statusClass;
        
        if (status === true || status === 'connected') {
            statusText = 'Connected';
            statusClass = 'connected';
        } else if (status === 'connecting') {
            statusText = 'Connecting...';
            statusClass = 'connecting';
        } else {
            statusText = 'Disconnected';
            statusClass = 'disconnected';
        }
        
        if (this.statusIndicator) {
            this.statusIndicator.textContent = statusText;
            this.statusIndicator.className = `status-indicator ${statusClass}`;
        }
    }
    
    /**
     * Scroll the chat container to the bottom
     */
    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }
    
    /**
     * Escape HTML special characters to prevent XSS
     * @param {string} unsafe - The string to escape
     * @returns {string} The escaped string
     */
    escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize the chat app when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('Initializing ChatApp...');
        window.chatApp = new ChatApp();
        console.log('ChatApp initialized successfully');
    } catch (error) {
        console.error('Failed to initialize ChatApp:', error);
    }
});
