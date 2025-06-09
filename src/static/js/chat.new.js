// chat.new.js - Main chat functionality with WebSocket support

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
        
        // Debug logging
        this.debugLog('ChatApp initializing...');
        this.setupDebugLogging();
        
        // Initialize WebSocket
        this.initializeWebSocket();
        
        // Set up UI elements
        this.setupUI();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Test WebSocket connection
        this.testWebSocketConnection();
        
        this.debugLog('ChatApp initialized');
    }
    
    async initialize() {
        this.setupEventListeners();
        this.setupSocket();
    }
    
    setupEventListeners() {
        // Form submission
        if (this.questionForm) {
            this.questionForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }
    }
    
    setupDebugLogging() {
        // Add debug container if it doesn't exist
        if (!document.getElementById('debug-container')) {
            const debugContainer = document.createElement('div');
            debugContainer.id = 'debug-container';
            debugContainer.style.position = 'fixed';
            debugContainer.style.bottom = '10px';
            debugContainer.style.right = '10px';
            debugContainer.style.zIndex = '1000';
            debugContainer.style.maxWidth = '300px';
            debugContainer.style.maxHeight = '200px';
            debugContainer.style.overflow = 'auto';
            debugContainer.style.padding = '10px';
            debugContainer.style.background = 'rgba(0, 0, 0, 0.8)';
            debugContainer.style.color = '#fff';
            debugContainer.style.borderRadius = '8px';
            debugContainer.style.fontFamily = 'monospace';
            debugContainer.style.fontSize = '12px';
            
            debugContainer.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <strong>WebSocket Debug</strong>
                    <div>
                        <button id="test-ws-btn" style="margin-right: 5px; padding: 3px 8px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">
                            Test
                        </button>
                        <button id="clear-log-btn" style="padding: 3px 8px; background: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">
                            Clear
                        </button>
                    </div>
                </div>
                <div id="ws-log" style="margin-top: 5px; padding: 5px; background: rgba(255, 255, 255, 0.1); border-radius: 4px; font-size: 11px; min-height: 20px; max-height: 150px; overflow-y: auto;">
                    [System] WebSocket debug log started\n
                </div>
                <div id="ws-status" style="margin-top: 5px; padding: 5px; background: #333; border-radius: 4px; font-size: 11px;">
                    Status: Initializing...
                </div>
            `;
            
            document.body.appendChild(debugContainer);
            
            // Add button handlers
            document.getElementById('test-ws-btn').addEventListener('click', () => this.testWebSocketConnection());
            document.getElementById('clear-log-btn').addEventListener('click', () => {
                const logElement = document.getElementById('ws-log');
                if (logElement) logElement.textContent = '[System] Log cleared\n';
            });
        }
    }
    
    logToDebug(message) {
        const logElement = document.getElementById('ws-log');
        if (logElement) {
            const timestamp = new Date().toLocaleTimeString();
            logElement.textContent += `[${timestamp}] ${message}\n`;
            logElement.scrollTop = logElement.scrollHeight;
        }
    }
    
    updateDebugStatus(message, type = 'info') {
        const statusElement = document.getElementById('ws-status');
        if (statusElement) {
            statusElement.textContent = `Status: ${message}`;
            
            // Reset previous status classes
            statusElement.className = '';
            statusElement.style.padding = '5px';
            statusElement.style.borderRadius = '4px';
            statusElement.style.fontSize = '11px';
            
            // Add appropriate class based on type
            if (type === 'success') {
                statusElement.style.background = '#4CAF50';
            } else if (type === 'error') {
                statusElement.style.background = '#f44336';
            } else if (type === 'warning') {
                statusElement.style.background = '#ff9800';
            } else {
                statusElement.style.background = '#333';
            }
        }
    }
    
    setupSocket() {
        this.logToDebug('[Chat] Initializing WebSocket connection...');
        this.updateDebugStatus('Connecting to server...', 'info');
        
        // Set up socket event handlers
        window.socketEvents = window.socketEvents || {};
        
        // Handle connection established
        window.socketEvents.onConnect = () => {
            console.log('[Chat] WebSocket connected');
            this.socket = window.socket;
            this.updateStatus('Connected');
            this.updateDebugStatus('Connected to server', 'success');
            this.addSystemMessage('Connected to chat server');
            
            // Test the connection
            this.testWebSocketConnection();
        };
        
        // Handle disconnection
        window.socketEvents.onDisconnect = (reason) => {
            console.log(`[Chat] WebSocket disconnected: ${reason}`);
            this.updateStatus('Disconnected');
            this.updateDebugStatus(`Disconnected: ${reason}`, 'error');
            this.removeTypingIndicator();
            this.addSystemMessage(`Disconnected from server: ${reason}`);
            
            // Try to reconnect if it was an unexpected disconnect
            if (reason !== 'io client disconnect') {
                setTimeout(() => {
                    console.log('[Chat] Attempting to reconnect...');
                    initializeWebSocket();
                }, 1000);
            }
        };
        
        // Handle errors
        window.socketEvents.onError = (error) => {
            console.error('[Chat] WebSocket error:', error);
            this.updateDebugStatus(`Error: ${error.message}`, 'error');
        };
        
        // Set up message handlers if socket exists
        if (window.socket) {
            this.socket = window.socket;
            
            // Handle new messages from the server
            this.socket.on('new_message', (data) => {
                console.log('[Chat] New message received:', data);
                this.updateDebugStatus('Received message from server', 'success');
                this.handleBotResponse(data);
            });
            
            // Handle message received acknowledgment
            this.socket.on('message_received', (data) => {
                console.log('[Chat] Message received by server:', data);
                this.updateDebugStatus('Server is processing your message...', 'info');
                this.showTypingIndicator();
            });
            
            // Handle test responses
            this.socket.on('test_response', (data) => {
                console.log('[Chat] Test response:', data);
                this.updateDebugStatus('Test successful!', 'success');
                this.addSystemMessage(`Test successful: ${JSON.stringify(data)}`);
            });
            
            // Handle typing indicators
            this.socket.on('typing', (data) => {
                if (data.is_typing) {
                    this.showTypingIndicator();
                } else {
                    this.removeTypingIndicator();
                }
            });
            
            // Handle errors
            this.socket.on('error', (error) => {
                const errorMsg = error.message || 'Unknown error occurred';
                console.error('[Chat] Error:', error);
                this.updateDebugStatus(`Error: ${errorMsg}`, 'error');
                this.addSystemMessage(`Error: ${errorMsg}`);
                this.removeTypingIndicator();
            });
        } else {
            console.warn('[Chat] WebSocket not available, initializing...');
            initializeWebSocket();
        }
        
        this.logToDebug(`[Chat] WebSocket status: ${window.socket?.connected ? 'Connected' : 'Disconnected'}`);
    }
    
    async testWebSocketConnection() {
        if (!window.socket || !window.socket.connected) {
            this.logToDebug('[Chat] Cannot test WebSocket: Not connected');
            return;
        }
        
        try {
            this.logToDebug('[Chat] Testing WebSocket connection...');
            this.updateDebugStatus('Testing connection...', 'info');
            
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Test timed out'));
                }, 5000);
                
                window.socket.emit('test', { test: 'connection' }, (response) => {
                    clearTimeout(timeout);
                    resolve(response);
                });
            });
            
            this.logToDebug('[Chat] WebSocket test successful');
            this.updateDebugStatus('Connection test passed', 'success');
        } catch (error) {
            const errorMsg = error.message || 'Unknown error';
            this.logToDebug(`[Chat] WebSocket test failed: ${errorMsg}`);
            this.updateDebugStatus(`Test failed: ${errorMsg}`, 'error');
            console.error('[Chat] WebSocket test failed:', error);
        }
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        const message = this.questionInput?.value?.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addUserMessage(message);
        
        // Clear input and focus it again
        if (this.questionInput) {
            this.questionInput.value = '';
            this.questionInput.focus();
        }
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Send message via WebSocket
        if (this.socket && this.socket.connected) {
            this.debugLog('Sending message:', message);
            
            // Emit typing start
            this.socket.emit('typing', {
                userId: this.socket.id,
                conversationId: this.currentConversationId
            });
            
            // Prepare message data
            const messageData = {
                message: message,
                conversation_id: this.currentConversationId,
                language: this.currentLanguage || 'en',
                timestamp: new Date().toISOString()
            };
            
            console.log('[Chat] Sending message:', messageData);
            this.updateDebugStatus('Sending message...', 'info');
            
            try {
                // Show typing indicator
                this.showTypingIndicator();
                
                // Add a timeout for the message sending
                const messageTimeout = setTimeout(() => {
                    if (this.isTyping) {
                        this.addSystemMessage('The server is taking longer than expected to respond. Please wait...', 'warning');
                    }
                }, 10000); // 10 seconds timeout
                
                // Send the message with acknowledgment
                this.socket.emit('new_message', messageData, (response) => {
                    // Clear the timeout
                    clearTimeout(messageTimeout);
                    
                    try {
                        // Handle the response from the server
                        if (response && response.status === 'success') {
                            this.debugLog('Message sent successfully:', response);
                            this.updateDebugStatus('Message sent successfully', 'success');
                            
                            // Handle bot response if any
                            if (response.message) {
                                this.addBotMessage(response.message);
                            }
                            
                            // Show suggestions if any
                            if (response.suggestions && response.suggestions.length > 0) {
                                this.showSuggestions(response.suggestions);
                            }
                        } else {
                            const errorMsg = response?.error || 'Unknown error';
                            console.error('Error sending message:', errorMsg);
                            this.addSystemMessage('Error sending message: ' + errorMsg, 'error');
                        }
                    } catch (error) {
                        console.error('Error handling message response:', error);
                        this.addSystemMessage('Error processing server response', 'error');
                    } finally {
                        // Emit stop typing and remove typing indicator
                        this.socket.emit('stop_typing', {
                            userId: this.socket.id,
                            conversationId: this.currentConversationId
                        });
                        this.removeTypingIndicator();
                    }
                });
                
            } catch (error) {
                console.error('Error in handleSubmit:', error);
                this.updateDebugStatus(`Error: ${error.message}`, 'error');
                this.addSystemMessage('An error occurred while sending your message. Please try again.', 'error');
                
                // Handle disconnection
                if (error.message && (error.message.includes('Not connected') || error.message.includes('disconnected'))) {
                    this.updateDebugStatus('Attempting to reconnect...', 'warning');
                    if (window.socket) {
                        window.socket.connect();
                    } else {
                        this.initializeWebSocket();
                    }
                }
                
                this.removeTypingIndicator();
            }
        } else {
            // Handle case when socket is not connected
            console.error('WebSocket is not connected');
            this.addSystemMessage('Not connected to the server. Please try again.', 'error');
            this.removeTypingIndicator();
            
            // Attempt to reconnect
            if (window.socket) {
                window.socket.connect();
            } else {
                this.initializeWebSocket();
            }
        }
    }
    
    addUserMessage(message) {
        this.addMessage('user', message);
    }
    
    addSystemMessage(message, type = 'info') {
        this.addMessage('system', message, type);
    }
    
    addMessage(sender, content, type = 'info') {
        if (!this.chatMessages) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message ${type}`;
        
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        contentElement.textContent = content;
        
        messageElement.appendChild(contentElement);
        this.chatMessages.appendChild(messageElement);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    showTypingIndicator() {
        if (this.typingIndicator) return;
        
        this.typingIndicator = document.createElement('div');
        this.typingIndicator.className = 'message bot-message typing-indicator';
        this.typingIndicator.innerHTML = `
            <div class="typing">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        
        this.chatMessages.appendChild(this.typingIndicator);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    removeTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.remove();
            this.typingIndicator = null;
        }
    }
    
    handleBotResponse(data) {
        this.removeTypingIndicator();
        
        if (data && data.message) {
            this.addMessage('bot', data.message);
            
            if (data.suggestions && data.suggestions.length > 0) {
                this.showSuggestions(data.suggestions);
            }
        }
    }
    
    showSuggestions(suggestions) {
        if (!this.suggestionsContainer) return;
        
        // Clear existing suggestions
        this.suggestionsContainer.innerHTML = '';
        
        // Add each suggestion as a button
        suggestions.forEach(suggestion => {
            const button = document.createElement('button');
            button.className = 'suggestion-btn';
            button.textContent = suggestion;
            button.addEventListener('click', () => {
                this.questionInput.value = suggestion;
                this.suggestionsContainer.innerHTML = '';
                this.questionInput.focus();
            });
            
            this.suggestionsContainer.appendChild(button);
        });
    }
    
    updateStatus(status) {
        if (this.statusIndicator) {
            this.statusIndicator.textContent = status;
        }
    }
    
    /**
     * Show typing indicator in the chat
     */
    showTypingIndicator() {
        // Don't show multiple typing indicators
        if (this.isTyping) return;
        
        this.isTyping = true;
        
        // Create typing indicator element if it doesn't exist
        if (!this.typingIndicator) {
            this.typingIndicator = document.createElement('div');
            this.typingIndicator.className = 'message bot-message typing-indicator';
            this.typingIndicator.id = 'typing-indicator';
            
            const typingContent = document.createElement('div');
            typingContent.className = 'message-content';
            
            const typingText = document.createElement('div');
            typingText.className = 'typing-text';
            typingText.textContent = 'Typing';
            
            const dots = document.createElement('div');
            dots.className = 'typing-dots';
            dots.innerHTML = '<span>.</span><span>.</span><span>.</span>';
            
            typingContent.appendChild(typingText);
            typingContent.appendChild(dots);
            this.typingIndicator.appendChild(typingContent);
            
            // Add to chat messages
            if (this.chatMessages) {
                this.chatMessages.appendChild(this.typingIndicator);
                this.scrollToBottom();
            }
        } else {
            // Make sure it's visible
            this.typingIndicator.style.display = 'flex';
        }
    }
    
    /**
     * Remove typing indicator from the chat
     */
    removeTypingIndicator() {
        this.isTyping = false;
        
        // Remove typing indicator if it exists
        if (this.typingIndicator) {
            // Fade out and remove
            this.typingIndicator.style.opacity = '0';
            this.typingIndicator.style.transition = 'opacity 0.3s ease';
            
            // Remove from DOM after fade out
            setTimeout(() => {
                if (this.typingIndicator && this.typingIndicator.parentNode) {
                    this.typingIndicator.parentNode.removeChild(this.typingIndicator);
                    this.typingIndicator = null;
                }
            }, 300);
        }
    }
    
    /**
     * Add a user message to the chat
     * @param {string} message - The message text
     * @param {string} [timestamp] - Optional timestamp
     */
    addUserMessage(message, timestamp) {
        if (!message || !this.chatMessages) return;
        
        // Remove typing indicator if it's visible
        this.removeTypingIndicator();
        
        // Create message element
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        
        // Add timestamp if provided
        const time = timestamp ? new Date(timestamp) : new Date();
        const timeString = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageElement.innerHTML = `
            <div class="message-content">
                <div class="message-text">${this.escapeHtml(message)}</div>
                <div class="message-time">${timeString}</div>
            </div>
            <div class="message-avatar">
                <i class="fas fa-user"></i>
            </div>
        `;
        
        // Add to chat
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
        
        // Save to message history
        this.saveMessageToHistory({
            type: 'user',
            content: message,
            timestamp: time.toISOString(),
            sender: 'user'
        });
    }
    
    /**
     * Add a bot message to the chat
     * @param {string} message - The message text
     * @param {string} [timestamp] - Optional timestamp
     */
    addBotMessage(message, timestamp) {
        if (!message || !this.chatMessages) return;
        
        // Remove typing indicator if it's visible
        this.removeTypingIndicator();
        
        // Create message element
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';
        
        // Add timestamp if provided
        const time = timestamp ? new Date(timestamp) : new Date();
        const timeString = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Process markdown if marked.js is available
        let messageContent = this.escapeHtml(message);
        if (window.marked) {
            try {
                messageContent = window.marked.parse(message);
            } catch (e) {
                console.error('Error parsing markdown:', e);
            }
        }
        
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${messageContent}</div>
                <div class="message-time">${timeString}</div>
            </div>
        `;
        
        // Add to chat
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
        
        // Save to message history
        this.saveMessageToHistory({
            type: 'bot',
            content: message,
            timestamp: time.toISOString(),
            sender: 'bot'
        });
        
        // Highlight code blocks if available
        this.highlightCodeBlocks(messageElement);
    }
    
    /**
     * Add a system message to the chat
     * @param {string} message - The message text
     * @param {string} [severity='info'] - Message severity (info, success, warning, error)
     * @param {string} [timestamp] - Optional timestamp
     */
    addSystemMessage(message, severity = 'info', timestamp) {
        if (!message || !this.chatMessages) return;
        
        // Create message element
        const messageElement = document.createElement('div');
        messageElement.className = `message system-message system-${severity}`;
        
        // Add timestamp if provided
        const time = timestamp ? new Date(timestamp) : new Date();
        const timeString = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Get icon based on severity
        let icon = 'info-circle';
        switch (severity) {
            case 'success':
                icon = 'check-circle';
                break;
            case 'warning':
                icon = 'exclamation-triangle';
                break;
            case 'error':
                icon = 'exclamation-circle';
                break;
            default:
                icon = 'info-circle';
        }
        
        messageElement.innerHTML = `
            <div class="message-icon">
                <i class="fas fa-${icon}"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${this.escapeHtml(message)}</div>
                <div class="message-time">${timeString}</div>
            </div>
        `;
        
        // Add to chat
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
        
        // Save to message history
        this.saveMessageToHistory({
            type: 'system',
            content: message,
            severity: severity,
            timestamp: time.toISOString(),
            sender: 'system'
        });
    }
    
    /**
     * Save a message to the conversation history
     * @param {Object} message - The message object to save
     */
    saveMessageToHistory(message) {
        if (!message) return;
        
        try {
            // Get existing history or initialize empty array
            const history = JSON.parse(localStorage.getItem('chatHistory') || '[]');
            
            // Add the new message
            history.push({
                ...message,
                // Ensure we have a timestamp
                timestamp: message.timestamp || new Date().toISOString()
            });
            
            // Keep only the last 100 messages to prevent localStorage overflow
            const maxHistory = 100;
            const trimmedHistory = history.slice(-maxHistory);
            
            // Save back to localStorage
            localStorage.setItem('chatHistory', JSON.stringify(trimmedHistory));
            
            this.debugLog('Message saved to history:', message);
        } catch (error) {
            console.error('Error saving message to history:', error);
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
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
    
    /**
     * Highlight code blocks in a message element
     * @param {HTMLElement} messageElement - The message element containing code blocks
     */
    highlightCodeBlocks(messageElement) {
        if (!messageElement || !window.hljs) return;
        
        try {
            // Find all code blocks in the message
            const codeBlocks = messageElement.querySelectorAll('pre code');
            
            if (codeBlocks.length > 0) {
                // Add copy button to each code block
                codeBlocks.forEach((codeBlock) => {
                    // Skip if already highlighted
                    if (codeBlock.classList.contains('hljs')) return;
                    
                    // Create container for code block and copy button
                    const container = document.createElement('div');
                    container.className = 'code-block-container';
                    
                    // Create copy button
                    const copyButton = document.createElement('button');
                    copyButton.className = 'copy-code-button';
                    copyButton.title = 'Copy to clipboard';
                    copyButton.innerHTML = '<i class="far fa-copy"></i>';
                    
                    // Handle copy button click
                    copyButton.addEventListener('click', () => {
                        const code = codeBlock.textContent;
                        navigator.clipboard.writeText(code).then(() => {
                            // Show copied feedback
                            const originalTitle = copyButton.title;
                            copyButton.innerHTML = '<i class="fas fa-check"></i>';
                            copyButton.title = 'Copied!';
                            
                            // Reset after 2 seconds
                            setTimeout(() => {
                                copyButton.innerHTML = '<i class="far fa-copy"></i>';
                                copyButton.title = originalTitle;
                            }, 2000);
                        }).catch(err => {
                            console.error('Failed to copy code:', err);
                        });
                    });
                    
                    // Wrap the code block with the container
                    const preElement = codeBlock.parentNode;
                    preElement.parentNode.insertBefore(container, preElement);
                    container.appendChild(preElement);
                    container.appendChild(copyButton);
                    
                    // Apply syntax highlighting
                    hljs.highlightElement(codeBlock);
                });
            }
        } catch (error) {
            console.error('Error highlighting code blocks:', error);
        }
    }
    
    /**
     * Show clickable suggestions below a message
     * @param {Array} suggestions - Array of suggestion strings
     */
    showSuggestions(suggestions) {
        if (!suggestions || !Array.isArray(suggestions) || suggestions.length === 0) {
            return;
        }
        
        try {
            // Create suggestions container
            const container = document.createElement('div');
            container.className = 'suggestions-container';
            
            // Add title
            const title = document.createElement('div');
            title.className = 'suggestions-title';
            title.textContent = 'Suggestions:';
            container.appendChild(title);
            
            // Add each suggestion as a button
            suggestions.forEach((suggestion, index) => {
                if (!suggestion) return;
                
                const button = document.createElement('button');
                button.className = 'suggestion-button';
                button.textContent = suggestion;
                
                // Handle suggestion click
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    
                    // Set the suggestion as the input value
                    if (this.questionInput) {
                        this.questionInput.value = suggestion;
                        this.questionInput.focus();
                        
                        // Trigger input event to update any listeners
                        const event = new Event('input', { bubbles: true });
                        this.questionInput.dispatchEvent(event);
                    }
                    
                    // Remove the suggestions
                    container.remove();
                });
                
                container.appendChild(button);
            });
            
            // Add to the DOM after the last message
            if (this.chatMessages && this.chatMessages.lastChild) {
                this.chatMessages.insertBefore(container, this.chatMessages.lastChild.nextSibling);
            } else if (this.chatMessages) {
                this.chatMessages.appendChild(container);
            }
            
            // Auto-scroll to show suggestions
            this.scrollToBottom();
            
        } catch (error) {
            console.error('Error showing suggestions:', error);
        }
    }
    
    /**
     * Scroll the chat container to the bottom
     */
    scrollToBottom() {
        if (!this.chatMessages) return;
        
        // Use requestAnimationFrame for smooth scrolling
        requestAnimationFrame(() => {
            try {
                // Scroll to bottom with smooth behavior
                this.chatMessages.scrollTo({
                    top: this.chatMessages.scrollHeight,
                    behavior: 'smooth'
                });
            } catch (e) {
                // Fallback for browsers that don't support scroll options
                try {
                    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                } catch (err) {
                    console.error('Error scrolling to bottom:', err);
                }
            }
        });
    }
    
    /**
     * Log debug messages to console and UI if debug mode is enabled
     * @param {...any} args - Arguments to log
     */
    debugLog(...args) {
        if (!this.debugEnabled) return;
        
        // Log to console
        console.log('[ChatApp]', ...args);
        
        // Add to debug panel if available
        const debugPanel = document.getElementById('debug-panel');
        if (debugPanel) {
            const message = document.createElement('div');
            message.className = 'debug-message';
            
            // Format the message with timestamps
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            const formattedArgs = args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
            ).join(' ');
            
            message.textContent = `[${timeString}] ${formattedArgs}`;
            
            // Add to the top of the debug panel
            if (debugPanel.firstChild) {
                debugPanel.insertBefore(message, debugPanel.firstChild);
            } else {
                debugPanel.appendChild(message);
            }
            
            // Limit the number of messages in the debug panel
            const maxMessages = 50;
            while (debugPanel.children.length > maxMessages) {
                debugPanel.removeChild(debugPanel.lastChild);
            }
        }
    }
    
    /**
     * Update the debug status message
     * @param {string} message - Status message
     * @param {string} [type='info'] - Message type (info, success, warning, error)
     */
    updateDebugStatus(message, type = 'info') {
        if (!this.debugEnabled) return;
        
        const statusElement = document.getElementById('debug-status');
        if (!statusElement) return;
        
        // Update status text and class
        statusElement.textContent = message;
        statusElement.className = `debug-status debug-status-${type}`;
        
        // Auto-clear after 5 seconds for non-error messages
        if (type !== 'error') {
            clearTimeout(this.debugStatusTimeout);
            this.debugStatusTimeout = setTimeout(() => {
                if (statusElement.textContent === message) {
                    statusElement.textContent = 'Ready';
                    statusElement.className = 'debug-status debug-status-info';
                }
            }, 5000);
        }
    }
    
    /**
     * Set up the chat UI elements
     */
    setupUI() {
        try {
            // Get or create chat container
            let chatContainer = document.querySelector('.chat-container');
            if (!chatContainer) {
                chatContainer = document.createElement('div');
                chatContainer.className = 'chat-container';
                document.body.appendChild(chatContainer);
            }
            
            // Set up chat messages container
            this.chatMessages = document.getElementById('chat-messages');
            if (!this.chatMessages) {
                this.chatMessages = document.createElement('div');
                this.chatMessages.id = 'chat-messages';
                this.chatMessages.className = 'chat-messages';
                chatContainer.appendChild(this.chatMessages);
            }
            
            // Set up input form
            this.questionForm = document.getElementById('question-form');
            if (!this.questionForm) {
                this.questionForm = document.createElement('form');
                this.questionForm.id = 'question-form';
                this.questionForm.className = 'chat-input-container';
                
                // Create input field
                this.questionInput = document.createElement('input');
                this.questionInput.type = 'text';
                this.questionInput.id = 'question-input';
                this.questionInput.placeholder = 'Type your message...';
                this.questionInput.autocomplete = 'off';
                
                // Create send button
                const sendButton = document.createElement('button');
                sendButton.type = 'submit';
                sendButton.className = 'send-button';
                sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
                sendButton.title = 'Send message';
                
                // Append elements
                this.questionForm.appendChild(this.questionInput);
                this.questionForm.appendChild(sendButton);
                chatContainer.appendChild(this.questionForm);
            } else {
                this.questionInput = document.getElementById('question-input');
            }
            
            // Set up connection status indicator
            let statusIndicator = document.getElementById('connection-status');
            if (!statusIndicator) {
                statusIndicator = document.createElement('div');
                statusIndicator.id = 'connection-status';
                statusIndicator.className = 'connection-status';
                document.body.appendChild(statusIndicator);
            }
            
            // Initialize debug panel if debug is enabled
            if (this.debugEnabled) {
                this.setupDebugPanel();
            }
            
            this.debugLog('UI setup complete');
        } catch (error) {
            console.error('Error setting up UI:', error);
        }
    }
    
    /**
     * Set up event listeners for the chat
     */
    setupEventListeners() {
        try {
            // Form submission
            if (this.questionForm) {
                this.questionForm.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.handleSubmit(e);
                });
            }
            
            // Input field events
            if (this.questionInput) {
                // Handle Enter key (but allow Shift+Enter for new lines)
                this.questionInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.handleSubmit(e);
                    }
                });
                
                // Auto-resize textarea (if it becomes one)
                this.questionInput.addEventListener('input', () => {
                    this.adjustTextareaHeight(this.questionInput);
                });
            }
            
            // Handle window resize
            window.addEventListener('resize', () => {
                this.adjustLayout();
            });
            
            // Handle beforeunload to clean up
            window.addEventListener('beforeunload', () => {
                this.cleanup();
            });
            
            this.debugLog('Event listeners set up');
        } catch (error) {
            console.error('Error setting up event listeners:', error);
        }
    }
    
    /**
     * Set up the debug panel for development
     */
    setupDebugPanel() {
        try {
            // Check if debug panel already exists
            let debugPanel = document.getElementById('debug-panel');
            if (debugPanel) return;
            
            // Create debug panel container
            debugPanel = document.createElement('div');
            debugPanel.id = 'debug-panel';
            debugPanel.className = 'debug-panel';
            
            // Create debug header
            const debugHeader = document.createElement('div');
            debugHeader.className = 'debug-header';
            debugHeader.innerHTML = `
                <h3>Debug Console</h3>
                <div id="debug-status" class="debug-status">Ready</div>
                <button id="debug-clear" class="debug-button" title="Clear console">
                    <i class="fas fa-trash-alt"></i>
                </button>
                <button id="debug-toggle" class="debug-button" title="Toggle panel">
                    <i class="fas fa-chevron-down"></i>
                </button>
            `;
            
            // Create debug content
            const debugContent = document.createElement('div');
            debugContent.id = 'debug-content';
            debugContent.className = 'debug-content';
            
            // Assemble the panel
            debugPanel.appendChild(debugHeader);
            debugPanel.appendChild(debugContent);
            document.body.appendChild(debugPanel);
            
            // Add event listeners for debug controls
            const clearButton = document.getElementById('debug-clear');
            const toggleButton = document.getElementById('debug-toggle');
            
            if (clearButton) {
                clearButton.addEventListener('click', () => {
                    debugContent.innerHTML = '';
                    this.debugLog('Debug console cleared');
                });
            }
            
            if (toggleButton) {
                toggleButton.addEventListener('click', () => {
                    debugContent.style.display = 
                        debugContent.style.display === 'none' ? 'block' : 'none';
                    const icon = toggleButton.querySelector('i');
                    if (icon) {
                        icon.className = debugContent.style.display === 'none' ? 
                            'fas fa-chevron-up' : 'fas fa-chevron-down';
                    }
                });
            }
            
            this.debugLog('Debug panel initialized');
        } catch (error) {
            console.error('Error setting up debug panel:', error);
        }
    }
    
    /**
     * Adjust the height of a textarea to fit its content
     * @param {HTMLTextAreaElement} textarea - The textarea to adjust
     */
    adjustTextareaHeight(textarea) {
        if (!textarea) return;
        
        try {
            // Reset height to get the correct scrollHeight
            textarea.style.height = 'auto';
            
            // Set the height to scrollHeight, but limit to max 150px
            const maxHeight = 150;
            const newHeight = Math.min(textarea.scrollHeight, maxHeight);
            
            // Apply the new height
            textarea.style.height = `${newHeight}px`;
            
            // Show/hide scrollbar based on content
            textarea.style.overflowY = newHeight >= maxHeight ? 'auto' : 'hidden';
        } catch (error) {
            console.error('Error adjusting textarea height:', error);
        }
    }
    
    /**
     * Adjust the layout based on window size
     */
    adjustLayout() {
        try {
            const isMobile = window.innerWidth <= 768;
            
            // Toggle mobile class on body
            document.body.classList.toggle('mobile-view', isMobile);
            
            // Adjust chat container height
            if (this.chatMessages) {
                const headerHeight = document.querySelector('header')?.offsetHeight || 0;
                const inputHeight = this.questionForm?.offsetHeight || 0;
                const windowHeight = window.innerHeight;
                
                // Set chat messages height to fill available space
                this.chatMessages.style.height = `${windowHeight - headerHeight - inputHeight - 40}px`; // 40px padding
                
                // Ensure we're scrolled to the bottom after layout changes
                this.scrollToBottom();
            }
            
            this.debugLog('Layout adjusted', { isMobile });
        } catch (error) {
            console.error('Error adjusting layout:', error);
        }
    }
    
    /**
     * Clean up event listeners and resources
     */
    cleanup() {
        try {
            // Disconnect WebSocket
            if (this.socket && this.socket.connected) {
                this.socket.disconnect();
                this.debugLog('WebSocket disconnected');
            }
            
            // Clear any pending timeouts
            if (this.typingTimeout) {
                clearTimeout(this.typingTimeout);
                this.typingTimeout = null;
            }
            
            if (this.reconnectTimeout) {
                clearTimeout(this.reconnectTimeout);
                this.reconnectTimeout = null;
            }
            
            if (this.debugStatusTimeout) {
                clearTimeout(this.debugStatusTimeout);
                this.debugStatusTimeout = null;
            }
            
            // Remove event listeners
            if (this.questionForm) {
                this.questionForm.replaceWith(this.questionForm.cloneNode(true));
            }
            
            // Clean up debug panel
            const debugPanel = document.getElementById('debug-panel');
            if (debugPanel) {
                debugPanel.remove();
            }
            
            this.debugLog('Cleanup complete');
        } catch (error) {
            console.error('Error during cleanup:', error);
        }
    }
    
    /**
     * Initialize the chat application
     * @param {Object} [options] - Configuration options
     * @param {boolean} [options.debug=false] - Enable debug mode
     * @param {string} [options.userId] - Current user ID
     * @param {string} [options.conversationId] - Conversation ID
     * @param {string} [options.serverUrl] - WebSocket server URL
     */
    async initialize(options = {}) {
        try {
            // Set options
            this.debugEnabled = !!options.debug;
            this.userId = options.userId || this.generateUserId();
            this.conversationId = options.conversationId || `conv_${Date.now()}`;
            this.serverUrl = options.serverUrl || window.location.origin;
            
            this.debugLog('Initializing chat application', {
                userId: this.userId,
                conversationId: this.conversationId,
                serverUrl: this.serverUrl,
                debug: this.debugEnabled
            });
            
            // Set up the UI
            this.setupUI();
            
            // Set up WebSocket connection
            this.initializeWebSocket();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Initial layout adjustment
            this.adjustLayout();
            
            // Focus the input field
            if (this.questionInput) {
                this.questionInput.focus();
            }
            
            // Load any existing conversation history
            this.loadConversationHistory();
            
            this.debugLog('Chat application initialized');
            this.updateDebugStatus('Ready', 'success');
            
        } catch (error) {
            console.error('Error initializing chat application:', error);
            this.updateDebugStatus('Initialization failed', 'error');
            
            // Show error to user
            this.addSystemMessage(
                'Failed to initialize chat. Please refresh the page to try again.',
                'error'
            );
        }
    }
    
    /**
     * Generate a unique user ID if one doesn't exist
     * @returns {string} A unique user ID
     */
    generateUserId() {
        try {
            // Try to get existing user ID from localStorage
            let userId = localStorage.getItem('chatUserId');
            
            // If no user ID exists, generate a new one
            if (!userId) {
                userId = `user_${Math.random().toString(36).substr(2, 9)}`;
                localStorage.setItem('chatUserId', userId);
                this.debugLog('Generated new user ID:', userId);
            }
            
            return userId;
        } catch (error) {
            // Fallback to a simple random ID if localStorage fails
            console.error('Error generating user ID:', error);
            return `user_${Math.random().toString(36).substr(2, 9)}`;
        }
    }
    
    /**
     * Update the connection status in the UI
     * @param {boolean} isConnected - Whether the WebSocket is connected
     */
    updateConnectionStatus(isConnected) {
        if (!this.connectionStatus) {
            this.connectionStatus = document.getElementById('connection-status');
        }
        
        if (this.connectionStatus) {
            this.connectionStatus.className = `connection-status ${isConnected ? 'connected' : 'disconnected'}`;
            this.connectionStatus.title = isConnected ? 'Connected to server' : 'Disconnected from server';
            this.connectionStatus.innerHTML = isConnected ? 
                '<i class="fas fa-circle"></i> Connected' : 
                '<i class="fas fa-circle"></i> Disconnected';
        }
        
        // Show a system message on connection state change
        if (isConnected !== this.wasConnected) {
            this.addSystemMessage(
                isConnected ? 'Connected to server' : 'Disconnected from server',
                isConnected ? 'success' : 'warning'
            );
            this.wasConnected = isConnected;
        }
        
    /**
     * Initialize WebSocket connection
     */
    initializeWebSocket() {
        // If socket already exists, disconnect it first
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        // Socket.IO connection options
        const socketOptions = {
            path: '/socket.io',
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            timeout: 20000,
            autoConnect: true
        };
        // Get WebSocket URL from data attribute or use current origin
        const wsUrl = document.documentElement.getAttribute('data-ws-url') || window.location.origin;
        // ... (rest of your connection logic here)
        // Example:
        this.socket = io(wsUrl, socketOptions);
        // Setup event handlers here
        this.setupSocketEventHandlers();
    }
                // Update current conversation ID if server provided a different one
                if (response.conversationId && response.conversationId !== this.currentConversationId) {
                    this.debugLog('Updated conversation ID:', response.conversationId);
                    this.currentConversationId = response.conversationId;
                }
                // Load conversation history if any
                if (response.history && response.history.length > 0) {
                    this.debugLog('Loading conversation history:', response.history.length, 'messages');
                    this.loadConversationHistory(response.history);
                }
            } else {
                const errorMsg = response?.error || 'Unknown error';
                console.error('Failed to join conversation:', errorMsg);
                this.addSystemMessage('Error joining conversation: ' + errorMsg, 'error');
            }
        });
    }

    // ... (rest of your methods remain unchanged)
    
    /**
     * Load conversation history
     * @param {Array} history - Conversation history
     */
    loadConversationHistory(history) {
        try {
            // Sort history by timestamp
            const sortedHistory = history.sort((a, b) => a.timestamp - b.timestamp);
    } catch (error) {
        console.error('Failed to initialize ChatApp:', error);
    }
});

        sortedHistory.forEach(message => {
            try {
                if (message.type === 'system') {
                    this.addSystemMessage(message.content, message.severity || 'info');
                } else if (message.sender === 'user') {
                    this.addUserMessage(message.content, message.timestamp);
                } else if (message.sender === 'bot' || message.sender === 'assistant') {
                    this.addBotMessage(message.content, message.timestamp);
                    
                    // Show suggestions if available
                    if (message.suggestions && message.suggestions.length > 0) {
                        // Small delay to ensure message is rendered first
                        setTimeout(() => {
                            this.showSuggestions(message.suggestions);
                        }, 100);
                    }
                }
            } catch (error) {
                console.error('Error loading message from history:', error, message);
            }
        });
        
        // Scroll to bottom to show latest messages
        this.scrollToBottom();
        
        this.debugLog('Loaded conversation history:', sortedHistory.length, 'messages');
    }
    
    /**
     * Initialize WebSocket connection
     */
    initializeWebSocket() {
        // If socket already exists, disconnect it first
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        
        // Check if Socket.IO is available
        if (!window.io) {
            console.error('Socket.IO client not loaded');
            this.addSystemMessage('Error: Chat features not available. Socket.IO client not loaded.', 'error');
            return;
        }
        
        this.debugLog('Initializing WebSocket connection...');
        
        // Configure socket options
        const socketOptions = {
            reconnection: true,
            reconnectionAttempts: this.maxReconnectAttempts,
            reconnectionDelay: this.reconnectDelay,
            reconnectionDelayMax: 10000, // 10 seconds max delay
            timeout: 20000,
            autoConnect: true,
            transports: ['websocket', 'polling'],
            upgrade: true,
            forceNew: true,
            withCredentials: true,
            path: '/socket.io',
            secure: window.location.protocol === 'https:',
            rejectUnauthorized: false
        };
        
        try {
            // Initialize socket
            this.socket = io(socketOptions);
            
            // Store socket instance globally for debugging
            window.chatSocket = this.socket;
            
            // Connection established
            this.socket.on('connect', () => {
                this.debugLog('WebSocket connected with ID:', this.socket.id);
                this.updateConnectionStatus(true);
                this.reconnectAttempts = 0; // Reset reconnect attempts on successful connection
                
                // Join the conversation room
                this.joinConversation();
                
                // Notify the user
                this.addSystemMessage('Connected to the chat server', 'success');
            });
            
            // Connection lost
            this.socket.on('disconnect', (reason) => {
                this.debugLog('WebSocket disconnected:', reason);
                this.updateConnectionStatus(false);
                
                // Only show message if we're not in the process of reconnecting
                if (this.reconnectAttempts === 0) {
                    this.addSystemMessage('Disconnected from the chat server. Attempting to reconnect...', 'warning');
                }
                
                // Implement exponential backoff for reconnection
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
                    this.debugLog(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
                    
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.socket.connect();
                    }, delay);
                } else {
                    this.addSystemMessage('Failed to reconnect to the server. Please refresh the page.', 'error');
                }
            });
            
            // Error handling
            this.socket.on('connect_error', (error) => {
                console.error('WebSocket connection error:', error);
                this.addSystemMessage('Connection error: ' + (error.message || 'Unknown error'), 'error');
                this.updateConnectionStatus(false);
            });
            
            // Handle successful reconnection
            this.socket.on('reconnect', (attemptNumber) => {
                this.debugLog('Successfully reconnected after', attemptNumber, 'attempts');
                this.addSystemMessage('Reconnected to the chat server', 'success');
                this.updateConnectionStatus(true);
                this.joinConversation();
            });
            
            // Handle reconnection attempts
            this.socket.on('reconnect_attempt', (attemptNumber) => {
                this.debugLog('Reconnection attempt', attemptNumber);
                this.updateStatus(`Reconnecting... (attempt ${attemptNumber}/${this.maxReconnectAttempts})`);
            });
            
            // Handle reconnection failure
            this.socket.on('reconnect_failed', () => {
                this.debugLog('Reconnection failed after', this.maxReconnectAttempts, 'attempts');
                this.addSystemMessage('Failed to reconnect to the server. Please refresh the page.', 'error');
                this.updateStatus('Disconnected');
            });
            
            // Handle incoming messages
            this.socket.on('new_message', (data) => {
                this.handleIncomingMessage(data);
            });
            
            // Handle message received acknowledgment
            this.socket.on('message_received', (data) => {
                this.debugLog('Server received message:', data);
                this.removeTypingIndicator();
            });
            
            // Handle typing indicators
            this.socket.on('typing', (data) => {
                if (data.userId !== this.socket.id) {
                    this.showTypingIndicator();
                }
            });
            
            // Handle stop typing
            this.socket.on('stop_typing', (data) => {
                if (data.userId !== this.socket.id) {
                    this.removeTypingIndicator();
                }
            });
            
        } catch (error) {
            console.error('Error initializing WebSocket:', error);
            this.addSystemMessage('Error initializing chat connection. Please refresh the page.', 'error');
            this.updateConnectionStatus(false);
        }
    }
    
    /**
     * Handle incoming WebSocket messages
     * @param {Object} data - The message data
     */
    handleIncomingMessage(data) {
        try {
            this.debugLog('Incoming message:', data);
            
            // Remove typing indicator if present
            this.removeTypingIndicator();
            
            if (!data) {
                console.error('Received empty message');
                return;
            }
            
            // Handle different message types
            if (data.type === 'message' || data.message) {
                // Regular chat message
                this.addBotMessage(data.message);
            } else if (data.type === 'error') {
                // Error message
                this.addSystemMessage(data.message || 'An error occurred', 'error');
            } else if (data.type === 'status') {
                // Status update
                this.updateStatus(data.message);
            } else if (data.type === 'suggestions' && data.suggestions) {
                // Show suggestions
                this.showSuggestions(data.suggestions);
            }
            
            // Handle conversation ID updates
            if (data.conversation_id && data.conversation_id !== this.currentConversationId) {
                this.debugLog('Updating conversation ID:', data.conversation_id);
                this.currentConversationId = data.conversation_id;
            }
            
            // Scroll to bottom to show new messages
            this.scrollToBottom();
            
        } catch (error) {
            console.error('Error handling incoming message:', error, data);
            this.debugLog('Loaded conversation history:', sortedHistory.length, 'messages');
    }
}
}

document.addEventListener('DOMContentLoaded', () => {
    try {
        window.chatApp = new ChatApp();
        if (window.chatApp && typeof window.chatApp.initializeWebSocket === 'function') {
            window.chatApp.initializeWebSocket();
        }
    } catch (error) {
        console.error('Failed to initialize ChatApp:', error);
    }
});

// ... (rest of the code remains the same)
