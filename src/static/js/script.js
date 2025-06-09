document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chat-messages');
    const questionForm = document.getElementById('question-form');
    const questionInput = document.getElementById('question-input');
    const suggestionsContainer = document.getElementById('suggestions-container');
    const refreshBtn = document.getElementById('refresh-btn');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const statusIndicator = document.getElementById('status-indicator');
    const themeSelect = document.getElementById('theme-select');

    // Initialize Socket.IO
    const socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        statusIndicator.textContent = 'Connected';
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        statusIndicator.textContent = 'Disconnected';
    });
    
    socket.on('ask_response', function(data) {
        console.log('Received bot response:', data);
        // Remove typing indicator
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        
        // Add bot response
        addBotMessage(data.response);
        
        // Display suggestions
        displaySuggestions(data.suggestions);
        
        statusIndicator.textContent = 'Ready';
    });

    // Theme handling
    if (themeSelect) {
        // Set initial value based on current theme
        const currentTheme = localStorage.getItem('theme') || 'system';
        themeSelect.value = currentTheme;
        
        themeSelect.addEventListener('change', function() {
            const selectedTheme = themeSelect.value;
            
            if (selectedTheme === 'system') {
                const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                document.documentElement.setAttribute('data-theme', systemPrefersDark ? 'dark' : 'light');
            } else {
                document.documentElement.setAttribute('data-theme', selectedTheme);
            }
            
            localStorage.setItem('theme', selectedTheme);
        });
    } else {
        // Fallback to toggle button
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);

        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }

    // Add a user message to the chat
    window.addUserMessage = function(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user';
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(text)}</p>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Add a bot message to the chat
    window.addBotMessage = function(text) {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }

        // Ensure text is always a string and provide fallback for empty responses
        text = (typeof text === 'string') ? text : (text ? String(text) : '');
        if (!text.trim()) {
            text = '[No response from assistant]';
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot';
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Add a system message to the chat
    window.addSystemMessage = function(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(text)}</p>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Show typing indicator
    window.showTypingIndicator = function() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }

    // Display suggestions
    window.displaySuggestions = function(suggestions) {
        suggestionsContainer.innerHTML = '';
        
        if (!suggestions || suggestions.length === 0) {
            return;
        }
        
        suggestions.forEach(suggestion => {
            const suggestionEl = document.createElement('div');
            suggestionEl.className = 'suggestion';
            suggestionEl.textContent = suggestion;
            suggestionEl.addEventListener('click', () => {
                questionInput.value = suggestion;
                questionForm.dispatchEvent(new Event('submit'));
            });
            suggestionsContainer.appendChild(suggestionEl);
        });
    }

    // Handle form submission
    questionForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question) return;
        
        // Clear input and suggestions
        questionInput.value = '';
        suggestionsContainer.innerHTML = '';
        
        // Add user message
        addUserMessage(question);
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send question via WebSocket
        socket.emit('ask', { question });
        
        statusIndicator.textContent = 'Processing...';
    });

    // Handle refresh button
    refreshBtn.addEventListener('click', async function() {
        try {
            statusIndicator.textContent = 'Refreshing...';
            addSystemMessage('Refreshing documents...');
            
            const response = await fetch('/api/refresh', {
                method: 'POST'
            });
            
            const data = await response.json();
            addSystemMessage(data.message);
            
            statusIndicator.textContent = data.status === 'success' ? 'Ready' : 'Error';
        } catch (error) {
            console.error('Error:', error);
            addSystemMessage('Error: Could not refresh documents. Please try again.');
            statusIndicator.textContent = 'Error';
        }
    });

    // Helper function to escape HTML
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Helper function to scroll chat to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});

