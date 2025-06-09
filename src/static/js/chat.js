// chat.js - Main chat functionality with WebSocket support

/**
 * ChatApp - Manages the chat interface and WebSocket communication
 * Fixed version with reliable WebSocket connection handling
 */

/**
 * ChatApp Class - Manages chat interface and WebSocket communication
 */
class ChatApp {
    constructor() {
        // Core properties
        this.socket = null;
        this.currentConversationId = `conv_${Date.now()}`;
        this.currentLanguage = 'en';
        this.isProcessing = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.debugEnabled = true;
        
        // DOM Elements - Safely get references with error handling
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
        
        // Log initialization start
        console.log('ChatApp: Initializing...');
        
        // Initialize debug logging
        this.setupDebugLogging();
        
        // Begin initialization
        this.initialize();
    }
    
    async initialize() {
        try {
            this.setupEventListeners();
            this.initializeWebSocket();
            await this.loadUserPreferences();
            await this.loadConversations();
            this.createNewConversation();
            
            // Set up periodic connection check
            setInterval(() => this.checkConnection(), 30000);
        } catch (error) {
            console.error('Error initializing chat:', error);
            this.showError('Failed to initialize chat. Please refresh the page.');
        }
    }
    
    /**
     * Initialize WebSocket connection
     */
    initializeWebSocket() {
        try {
            // Close existing connection if any
            if (this.socket) {
                this.socket.disconnect();
                this.socket = null;
            }
            
            this.debugLog('Initializing WebSocket connection...');
            
            // Get the current host and protocol
            const protocol = window.location.protocol;
            const host = window.location.host;
            const wsUrl = protocol + '//' + host;
            
            this.debugLog(`Connecting to WebSocket server at ${wsUrl}`);
            
            // Create a Socket.IO instance with optimized settings
            this.socket = io(wsUrl, {
                // Basic connection settings
                path: '/socket.io',
                transports: ['websocket', 'polling'], // Match server configuration (websocket first, then fallback to polling)
                upgrade: true,
                rememberUpgrade: true,
                
                // Reconnection settings
                reconnection: true,
                reconnectionAttempts: this.maxReconnectAttempts,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                randomizationFactor: 0.5,
                timeout: 20000,
                autoConnect: true,
                
                // Security settings
                withCredentials: true,
                
                // Additional headers
                extraHeaders: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            this.debugLog('Socket.IO client created, connecting...');
            
            // Set up event handlers
            this.setupSocketHandlers();
            
            // Update status indicator
            this.updateConnectionStatus('connecting');
            
        } catch (error) {
            console.error('Error initializing WebSocket:', error);
            this.showError(`Failed to connect: ${error.message}. Retrying in 5 seconds...`);
            this.updateConnectionStatus('error');
            
            // Schedule retry with increasing delay
            this.reconnectAttempts++;
            const delay = Math.min(30000, 1000 * Math.pow(1.5, this.reconnectAttempts));
            this.debugLog(`Scheduling reconnection attempt in ${delay}ms`);
            setTimeout(() => this.initializeWebSocket(), delay);
        }
    }
    
    /**
     * Set up WebSocket event handlers
     */
    setupSocketHandlers() {
        if (!this.socket) {
            console.error('Cannot set up handlers - socket is null');
            return;
        }
        
        // Connection established
        this.socket.on('connect', () => {
            console.log(`Socket.IO connected (id: ${this.socket.id})`);
            this.debugLog('WebSocket connection established');
            this.updateConnectionStatus('connected');
            this.hideError();
            this.reconnectAttempts = 0; // Reset reconnect counter on successful connection
            
            // Join conversation room on connection
            this.joinConversation();
            
            // Show success message to user
            this.showStatus('Connected to chat server');
        });
        
        // Connection error
        this.socket.on('connect_error', (error) => {
            console.error('Socket.IO connection error:', error);
            this.debugLog(`WebSocket connection error: ${error.message}`);
            this.updateConnectionStatus('error');
            this.showError(`Connection error: ${error.message}. Attempting to reconnect...`);
        });
        
        // Disconnected
        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket disconnected:', reason);
            this.debugLog(`WebSocket disconnected: ${reason}`);
            this.updateConnectionStatus('disconnected');
            this.showStatus('Disconnected from chat server');
            
            // Auto-reconnect for certain disconnect reasons
            if (reason === 'io server disconnect' || reason === 'transport close') {
                setTimeout(() => {
                    this.debugLog('Attempting to reconnect after server disconnect');
                    this.socket.connect();
                }, 1000);
            }
        });
        
        // Reconnect attempts
        this.socket.io.on('reconnect_attempt', (attemptNumber) => {
            this.debugLog(`WebSocket reconnect attempt ${attemptNumber}/${this.maxReconnectAttempts}`);
            this.updateConnectionStatus('connecting');
            this.showStatus(`Reconnecting to server (attempt ${attemptNumber}/${this.maxReconnectAttempts})...`);
        });
        
        // Reconnect success
        this.socket.io.on('reconnect', (attemptNumber) => {
            console.log(`WebSocket reconnected after ${attemptNumber} attempts`);
            this.debugLog(`WebSocket reconnected after ${attemptNumber} attempts`);
            this.updateConnectionStatus('connected');
            this.hideError();
            this.joinConversation();
            this.showStatus('Reconnected to chat server');
        });
        
        // Reconnect error
        this.socket.io.on('reconnect_error', (error) => {
            console.error('WebSocket reconnect error:', error);
            this.debugLog(`WebSocket reconnect error: ${error.message}`);
        });
        
        // Reconnect failed
        this.socket.io.on('reconnect_failed', () => {
            this.debugLog('WebSocket reconnection failed after all attempts');
            this.updateConnectionStatus('failed');
            this.showError('Failed to reconnect to the server. Please refresh the page.');
        });
        
        // Message handlers
        this.socket.on('new_message', (data) => {
            this.debugLog('Received new_message event', data);
            if (data.conversation_id === this.currentConversationId) {
                this.addMessage(data.message, data.user_id !== 'bot', data.timestamp);
                
                if (data.user_id === 'bot') {
                    // Bot response received - update UI
                    this.isProcessing = false;
                    this.hideTypingIndicator();
                    this.questionInput.disabled = false;
                    this.questionInput.focus();
                    
                    // Show suggestions if available
                    if (data.suggestions && Array.isArray(data.suggestions) && data.suggestions.length > 0) {
                        this.showSuggestions(data.suggestions);
                    } else {
                        this.hideSuggestions();
                    }
                }
            }
        });
        
        this.socket.on('typing', (data) => {
            if (data.conversation_id === this.currentConversationId) {
                this.showTypingIndicator(data.is_typing);
            }
        });
        
        this.socket.on('message_received', (data) => {
            this.debugLog('Server received message', data);
            if (data.conversation_id === this.currentConversationId) {
                this.showStatus('Processing your message...');
            }
        });
        
        this.socket.on('error', (error) => {
            console.error('WebSocket error:', error);
            this.showError(error.message || 'An error occurred');
            this.isProcessing = false;
            this.hideTypingIndicator();
            this.questionInput.disabled = false;
        });
    }
    
    /**
     * Join a conversation room via WebSocket
     */
    joinConversation() {
        if (!this.socket || !this.socket.connected) {
            console.warn('Cannot join conversation - socket not connected');
            return;
        }
        
        const conversationId = this.currentConversationId;
        this.debugLog(`Joining conversation room: ${conversationId}`);
        
        this.socket.emit('join_conversation', { conversation_id: conversationId }, (response) => {
            if (response && response.success) {
                this.debugLog(`Successfully joined conversation: ${conversationId}`);
                this.addSystemMessage(`Connected to conversation: ${conversationId}`);
            } else {
                const errorMsg = response ? response.error : 'Unknown error';
                console.error('Failed to join conversation:', errorMsg);
                this.showError(`Failed to join conversation: ${errorMsg}`);
            }
        });
    }
       /**
     * Handle incoming WebSocket messages
     * @param {string} type - Message type
     * @param {Object} data - Message data
     */
    handleIncomingMessage(type, data) {
        try {
            this.debugLog(`Received ${type} message:`, data);
            
            // Validate conversation ID to prevent cross-talk
            if (data.conversation_id && data.conversation_id !== this.currentConversationId) {
                this.debugLog(`Ignoring message for different conversation: ${data.conversation_id}`);
                return;
            }
            
            switch (type) {
                case 'new_message':
                    // Process new message from server
                    if (data.message) {
                        const isBot = data.user_id === 'bot' || data.sender === 'bot';
                        
                        // Add the message to the UI
                        this.addMessage(
                            data.message, 
                            !isBot,  // isUser = !isBot 
                            data.timestamp || new Date().toISOString()
                        );
                        
                        // Handle end of message processing
                        if (isBot) {
                            // Bot response received - update UI
                            this.isProcessing = false;
                            this.hideTypingIndicator();
                            this.questionInput.disabled = false;
                            this.questionInput.focus();
                            
                            // Show suggestions if available
                            if (data.suggestions && Array.isArray(data.suggestions) && data.suggestions.length > 0) {
                                this.showSuggestions(data.suggestions);
                            } else {
                                this.hideSuggestions();
                            }
                        }
                    }
                    break;
                    
                case 'typing':
                    // Show typing indicator when bot is typing
                    if (data.is_typing || (data.sender === 'bot' && data.typing)) {
                        this.showTypingIndicator();
                    } else {
                        this.hideTypingIndicator();
                    }
                    break;
                    
                case 'stop_typing':
                    this.hideTypingIndicator();
                    break;
                    
                case 'message_received':
                    // Server acknowledged our message
                    this.debugLog('Server received message:', data);
                    this.showStatus('Processing your message...');
                    break;
                    
                case 'error':
                    this.showError(data.message || 'An error occurred');
                    this.isProcessing = false;
                    this.hideTypingIndicator();
                    this.questionInput.disabled = false;
                    break;
                    
                default:
                    console.warn('Unknown message type:', type);
            }
        } catch (error) {
            console.error('Error handling message:', error, { type, data });
            this.debugLog(`Error handling ${type} message: ${error.message}`);
            this.showError('Error processing message');
        }
    }

    /**
     * Update connection status in UI
     * @param {string|boolean} status - Connection status ('connected', 'disconnected', 'error', 'connecting', etc.)
     */
    updateConnectionStatus(status) {
        if (!this.statusIndicator) return;
        
        // Handle both boolean and string status values
        let statusClass = 'disconnected';
        let statusTitle = 'Disconnected';
        
        if (typeof status === 'boolean') {
            // Legacy boolean parameter support
            statusClass = status ? 'connected' : 'disconnected';
            statusTitle = status ? 'Connected' : 'Disconnected';
        } else {
            // New string-based status values
            switch (status) {
                case 'connected':
                    statusClass = 'connected';
                    statusTitle = 'Connected';
                    break;
                case 'connecting':
                    statusClass = 'connecting';
                    statusTitle = 'Connecting...';
                    break;
                case 'error':
                    statusClass = 'error';
                    statusTitle = 'Connection Error';
                    break;
                case 'failed':
                    statusClass = 'failed';
                    statusTitle = 'Connection Failed';
                    break;
                case 'disconnected':
                default:
                    statusClass = 'disconnected';
                    statusTitle = 'Disconnected';
            }
        }
        
        this.statusIndicator.className = `status-indicator ${statusClass}`;
        this.statusIndicator.title = statusTitle;
        
        // Log status change
        this.debugLog(`Connection status: ${statusTitle}`);
    }
    
    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'flex';
        } else {
            this.typingIndicator = document.createElement('div');
            this.typingIndicator.className = 'typing-indicator';
            this.typingIndicator.innerHTML = `
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            `;
            this.chatMessages.appendChild(this.typingIndicator);
        }
        this.scrollToBottom();
    }
    
    /**
     * Remove typing indicator
     */
    removeTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
        }
    }
    
    /**
     * Show status message
     * @param {string} message - Status message
     * @param {string} [type='info'] - Message type (info, success, warning, error)
     */
    showStatus(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        // You can add UI notification here if needed
    }
    
    /**
     * Show error message
     * @param {string} message - Error message
     */
    showError(message) {
        console.error(`[ERROR] ${message}`);
        this.showStatus(message, 'error');
    }
    
    /**
     * Check WebSocket connection status
     */
    checkConnection() {
        if (!this.socket || !this.socket.connected) {
            console.warn('WebSocket not connected, attempting to reconnect...');
            this.initializeWebSocket();
        }
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
        this.updateStatus('Connecting to server...');
        
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
                    Status: Connecting...
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
        
        // Initialize WebSocket event handlers
        window.socketEvents = window.socketEvents || {};
        
        // Set up socket event handlers
        window.socketEvents.onConnect = () => {
            console.log('[Chat] WebSocket connected');
            this.socket = window.socket;
            this.updateStatus('Connected');
            this.updateDebugStatus('Connected to server', 'success');
            this.addSystemMessage('Connected to chat server');
            
            // Test the connection
            this.testWebSocketConnection();
        };
        
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
        
        window.socketEvents.onError = (error) => {
            console.error('[Chat] WebSocket error:', error);
            this.updateDebugStatus(`Error: ${error.message}`, 'error');
        };
        
        // Set up message handlers
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
        
        // Log the connection status
        this.logToDebug(`[Chat] WebSocket status: ${window.socket?.connected ? 'Connected' : 'Disconnected'}`);
        
        // Add global socket access for debugging
        window.socket = this.socket;
    }
    
    updateStatus(status) {
        if (this.statusIndicator) {
            this.statusIndicator.textContent = status;
            // Update status indicator color based on status
            const colors = {
                'Connected': '#4CAF50',
                'Disconnected': '#f44336',
                'Connecting...': '#FFC107',
                'Connection error': '#f44336',
                'Connected to server': '#4CAF50',
                'Server is processing your message...': '#2196F3',
                'Error': '#f44336'
            };
            this.statusIndicator.style.color = colors[status] || '#000';
            
            // Also update the debug status if it exists
            if (this.updateDebugStatus) {
                const statusLower = status.toLowerCase();
                const type = statusLower.includes('error') ? 'error' : 
                             statusLower.includes('connect') ? 'success' : 'info';
                this.updateDebugStatus(status, type);
            }
        }
    }
    
    // Helper method to update debug status
    updateDebugStatus(message, type = 'info') {
        const statusElement = document.getElementById('ws-status');
        if (statusElement) {
            statusElement.textContent = `Status: ${message}`;
            statusElement.style.color = type === 'error' ? '#ff4444' : '#4CAF50';
        }
    }
    
    // Helper method to log messages to the debug console
    logToDebug(message) {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        const logElement = document.getElementById('ws-log');
        
        if (logElement) {
            // Create a new log entry
            const logEntry = document.createElement('div');
            logEntry.textContent = `[${timeString}] ${message}`;
            logEntry.style.padding = '2px 0';
            logEntry.style.borderBottom = '1px solid rgba(255, 255, 255, 0.1)';
            
            // Add the new entry to the top of the log
            logElement.prepend(logEntry);
            
            // Limit the number of log entries to prevent performance issues
            const maxLogEntries = 50;
            while (logElement.children.length > maxLogEntries) {
                logElement.removeChild(logElement.lastChild);
            }
        }
        
        // Also log to console
        console.log(`[DEBUG] ${message}`);
    }
    
    // Test WebSocket connection
    testWebSocketConnection() {
        if (!this.socket || !this.socket.connected) {
            this.updateDebugStatus('Not connected to WebSocket', 'error');
            return;
        }
        
        this.updateDebugStatus('Testing connection...', 'info');
        
        // Send a test message
        this.socket.emit('test', { 
            message: 'Test message',
            timestamp: new Date().toISOString()
        }, (response) => {
            console.log('Test callback response:', response);
        });
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        const question = this.questionInput.value.trim();
        if (!question || this.isProcessing) return;
        
        this.isProcessing = true;
        this.questionInput.value = '';
        this.addUserMessage(question);
        
        try {
            // Ensure we have a socket connection
            if (!window.socket || !window.socket.connected) {
                // Try to reconnect if not connected
                if (window.socket) {
                    window.socket.connect();
                    // Wait a bit for connection
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                    if (!window.socket.connected) {
                        throw new Error('Not connected to the server. Please check your connection and try again.');
                    }
                } else {
                    throw new Error('WebSocket not initialized. Please refresh the page.');
                }
            }
            
            const messageData = {
                message: question,
                conversation_id: this.currentConversationId || 'default-conversation',
                language: this.currentLanguage || 'en',
                timestamp: new Date().toISOString()
            };
            
            console.log('[Chat] Sending message:', messageData);
            this.updateDebugStatus('Sending message...', 'info');
            
            // Show typing indicator
            this.showTypingIndicator();
            
            // Send the message with a timeout
            const sendMessage = () => {
                return new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => {
                        reject(new Error('Message sending timed out. Please try again.'));
                    }, 10000); // 10 seconds timeout
                    
                    window.socket.emit('new_message', messageData, (response) => {
                        clearTimeout(timeout);
                        console.log('[Chat] Message sent successfully:', response);
                        this.updateDebugStatus('Message sent successfully', 'success');
                        resolve(response);
                    });
                });
            };
            
            await sendMessage();
            
        } catch (error) {
            const errorMsg = error.message || 'Unknown error occurred';
            console.error('[Chat] Error sending message:', error);
            this.updateDebugStatus(`Error: ${errorMsg}`, 'error');
            this.addSystemMessage(`Failed to send message: ${errorMsg}`);
            
            // Try to reconnect if disconnected
            if (error.message.includes('Not connected') || error.message.includes('disconnected')) {
                this.updateDebugStatus('Attempting to reconnect...', 'warning');
                if (window.socket) {
                    window.socket.connect();
                } else {
                    this.initializeWebSocket();
                }
            }
        } finally {
            this.isProcessing = false;
        }
    }
    
    handleBotResponse(data) {
        this.isProcessing = false;
        this.removeTypingIndicator();
        
        if (data.message) {
            this.addBotMessage(data.message);
        } else if (data.error) {
            this.addSystemMessage(`Error: ${data.error}`);
        }
        
        if (data.suggestions && data.suggestions.length > 0) {
            this.displaySuggestions(data.suggestions);
        }
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
        
        // Create message container
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        // Create content container
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Format the message based on its type
        if (type === 'bot') {
            // For bot messages, we might want to preserve formatting
            contentDiv.innerHTML = this.formatBotMessage(text);
        } else {
            // For user and system messages, use textContent to prevent XSS
            // But first, escape any HTML to prevent XSS
            contentDiv.textContent = text;
        }
        
        // Add timestamp
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatBotMessage(text) {
        if (!text) return '';
        
        // First, escape any HTML to prevent XSS
        const escapeHtml = (unsafe) => {
            return unsafe
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        };
        
        // Escape the text first
        let formatted = escapeHtml(text);
        
        // Convert markdown-style formatting to HTML
        // Bold: **text** to <strong>text</strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic: *text* to <em>text</em>
        formatted = formatted.replace(/(^|\s)\*(.*?)\*(?=\s|$)/g, '$1<em>$2</em>');
        
        // Code blocks: `code` to <code>code</code>
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Preserve line breaks
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Convert URLs to clickable links (only for http/https URLs)
        const urlRegex = /(https?:\/\/[^\s<]+[^<.,:;\"')\]\s])/g;
        formatted = formatted.replace(urlRegex, url => {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
        });
        
        return formatted;
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
