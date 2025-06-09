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
    
    // Theme handling
    function setupTheme() {
        if (themeSelect) {
            // Set initial value based on current theme
            const currentTheme = localStorage.getItem('theme') || 'system';
            themeSelect.value = currentTheme;
            
            // Apply theme
            const applyTheme = (theme) => {
                if (theme === 'system') {
                    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                    document.documentElement.setAttribute('data-theme', systemPrefersDark ? 'dark' : 'light');
                } else {
                    document.documentElement.setAttribute('data-theme', theme);
                }
            };
            
            // Initial theme application
            applyTheme(currentTheme);
            
            // Listen for theme changes
            themeSelect.addEventListener('change', function() {
                const selectedTheme = themeSelect.value;
                applyTheme(selectedTheme);
                localStorage.setItem('theme', selectedTheme);
            });
            
            // Listen for system theme changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
                if (themeSelect.value === 'system') {
                    applyTheme('system');
                }
            });
        } else if (themeToggleBtn) {
            // Fallback to toggle button if theme select is not available
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);

            themeToggleBtn.addEventListener('click', () => {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'light' ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
            });
        }
    }
    
    // Initialize theme
    setupTheme();
    
    // Make these functions globally available for chat.js
    window.addUserMessage = function(text) {
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(text)}</p>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    };
    
    window.addBotMessage = function(text) {
        if (!chatMessages) return;
        
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    };
    
    window.addSystemMessage = function(text, type = 'info') {
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message system-message ${type}`;
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
        if (!chatMessages) return null;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
        return typingDiv;
    };
    
    // Remove typing indicator
    window.removeTypingIndicator = function() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
            return true;
        }
        return false;
    };
    
    // Display suggestions
    window.displaySuggestions = function(suggestions) {
        if (!suggestions || !suggestions.length || !suggestionsContainer) return;
        
        suggestionsContainer.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const button = document.createElement('button');
            button.className = 'suggestion';
            button.textContent = suggestion;
            button.addEventListener('click', () => {
                if (questionInput) {
                    questionInput.value = suggestion;
                    questionInput.focus();
                }
                suggestionsContainer.innerHTML = '';
            });
            suggestionsContainer.appendChild(button);
        });
    };

    // Helper function to escape HTML
    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return String(unsafe)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Helper function to scroll chat to bottom
    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // Initialize chat app if the chat container exists
    if (document.getElementById('chat-container')) {
        // The ChatApp class will handle the WebSocket connection
        window.chatApp = window.chatApp || new window.ChatApp();
    }

    // Handle form submission if the form exists
    if (questionForm) {
        questionForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const question = questionInput?.value?.trim();
            if (!question) return;

            // If chat app is initialized, let it handle the submission
            if (window.chatApp && typeof window.chatApp.handleSubmit === 'function') {
                window.chatApp.handleSubmit(e);
            } else {
                // Fallback to simple message display
                window.addUserMessage(question);
                window.addBotMessage("I'm sorry, the chat functionality is not fully loaded yet. Please try again in a moment.");
                questionInput.value = '';
            }
        });
    }

    // Make sure the chat container is scrolled to bottom on load
    setTimeout(scrollToBottom, 100);
});
