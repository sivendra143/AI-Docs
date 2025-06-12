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
    window.addUserMessage = function(text, lang = 'EN') {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex flex-row-reverse flex items-end gap-3 animate-fade-in mt-2';
        
        const innerDiv = document.createElement('div');
        innerDiv.className = 'message user flex flex-row-reverse items-end gap-3 self-end animate-fade-in mb-4';
        
        innerDiv.innerHTML = `
            <div class="rounded-full bg-purple-200 dark:bg-purple-800 text-purple-700 dark:text-purple-200 p-3 shadow">
                🧑
            </div>
            <div class="bg-gradient-to-br from-purple-500 to-blue-500 dark:from-purple-700 dark:to-blue-700 rounded-2xl px-5 py-3 shadow text-white dark:text-blue-100 font-semibold border border-purple-300 dark:border-purple-900" style="text-shadow:0 1px 6px rgba(0,0,0,0.14); min-width:120px;">
                <p>${escapeHtml(text)}</p>
            </div>
        `;
        messageDiv.appendChild(innerDiv);
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Add a bot message to the chat
    window.addBotMessage = function(text, lang = 'HI') {
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
        messageDiv.className = 'flex items-start gap-3 animate-fade-in mt-2';
        
        const innerDiv = document.createElement('div');
        innerDiv.className = 'message bot flex items-start gap-3 animate-fade-in mt-2';
        
        innerDiv.innerHTML = `
            <div class="rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 p-3 shadow">
                🤖
            </div>
            <div class="bg-white/90 dark:bg-blue-900/90 backdrop-blur-md rounded-2xl px-5 py-3 shadow text-gray-800 dark:text-blue-100 border border-blue-200 dark:border-blue-800 relative">
                <p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>
                <div style="margin-top:0.6em; display:flex; align-items:center; gap:0.5em;">
                  <button class="translate-btn" style="background:linear-gradient(90deg,#6366f1 60%,#43a047 100%); color:#fff; border:none; border-radius:0.7em; padding:0.2em 0.9em; font-size:0.89em; cursor:pointer; box-shadow:0 1px 4px #6366f122;">Translate</button>
                  <select class="translate-lang" style="border-radius:0.7em; padding:0.15em 0.7em; font-size:0.92em; border:1px solid #e0e0e0;"></select>
                </div>
                <div class="translated-text" style="margin-top:0.5em; padding:0.6em; border-radius:0.7em; background-color:#f1f8e9; display:none;"></div>
            </div>
        `;
        messageDiv.appendChild(innerDiv);
        chatMessages.appendChild(messageDiv);
        messageDiv.classList.add('fade-in');
        // Translate button logic
        const translateBtn = messageDiv.querySelector('.translate-btn');
        const translateLangSelect = messageDiv.querySelector('.translate-lang');
        const translatedText = messageDiv.querySelector('.translated-text');
        // Language options
        const langOptions = [
            {value: 'en', label: '🇺🇸 English'},
            {value: 'hi', label: '🇮🇳 Hindi'},
            {value: 'te', label: '🇮🇳 Telugu'},
            {value: 'es', label: '🇪🇸 Spanish'},
            {value: 'fr', label: '🇫🇷 French'},
            {value: 'de', label: '🇩🇪 German'},
            {value: 'zh', label: '🇨🇳 Chinese'},
            {value: 'ja', label: '🇯🇵 Japanese'},
            {value: 'ru', label: '🇷🇺 Russian'},
            {value: 'it', label: '🇮🇹 Italian'},
            {value: 'pt', label: '🇵🇹 Portuguese'},
            {value: 'ar', label: '🇸🇦 Arabic'},
            {value: 'ko', label: '🇰🇷 Korean'},
            {value: 'tr', label: '🇹🇷 Turkish'},
            {value: 'nl', label: '🇳🇱 Dutch'},
            {value: 'el', label: '🇬🇷 Greek'},
            {value: 'id', label: '🇮🇩 Indonesian'},
            {value: 'vi', label: '🇻🇳 Vietnamese'},
            {value: 'th', label: '🇹🇭 Thai'},
            {value: 'pl', label: '🇵🇱 Polish'},
            {value: 'sv', label: '🇸🇪 Swedish'}
        ];
        // Get last used language or default
        const lastLang = localStorage.getItem('last_translate_lang') || 'en';
        langOptions.forEach(opt => {
            const o = document.createElement('option');
            o.value = opt.value;
            o.textContent = opt.label;
            if (opt.value === lastLang) o.selected = true;
            translateLangSelect.appendChild(o);
        });
        translateLangSelect.addEventListener('change', function() {
            localStorage.setItem('last_translate_lang', this.value);
        });
        translateBtn.addEventListener('click', function() {
            translateBtn.disabled = true;
            translateBtn.textContent = 'Translating...';
            const targetLang = translateLangSelect.value;
            // Use local backend translation proxy for reliability
            fetch('/api/translate', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ text: text, target: targetLang })
            })
            .then(res => res.json())
            .then(data => {
              if (data && data.translatedText) {
                translatedText.innerHTML = `<span class='message-label' style='color:#388e3c;'>${escapeHtml(data.translatedText)}</span>`;
                translatedText.style.display = 'block';
              } else {
                throw new Error('Translation failed');
              }
              translateBtn.disabled = false;
              translateBtn.textContent = 'Translate';
              translateLangSelect.disabled = false;
            })
            .catch(async () => {
                const googleUrl = `https://translate.google.com/?sl=auto&tl=${targetLang}&text=${encodeURIComponent(text)}&op=translate`;
                translatedText.innerHTML = `
                  <span class='message-label' style='color:#e53935;'>🌐 AI Translation unavailable</span><br>
                  <span style='color:#555; font-size:0.97em;'>This feature uses advanced AI for instant multilingual support, but the translation service is currently unreachable. Please try again later, or use the link below:</span><br>
                  <a href='${googleUrl}' target='_blank' style='color:#1976d2; text-decoration:underline; font-size:0.98em;'>Translate with Google</a>
                `;
                translatedText.style.display = 'block';
                translateBtn.disabled = false;
                translateBtn.textContent = 'Translate';
                translateLangSelect.disabled = false;
            });
        });
        scrollToBottom();
    }

    // Add a system message to the chat
    window.addSystemMessage = function(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start gap-3 animate-fade-in mt-2';
        
        const innerDiv = document.createElement('div');
        innerDiv.className = 'message system flex items-start gap-3 animate-fade-in mt-2';
        
        innerDiv.innerHTML = `
            <div class="rounded-full bg-yellow-100 dark:bg-yellow-900 text-yellow-600 dark:text-yellow-300 p-3 shadow">
                💡
            </div>
            <div class="bg-white/90 dark:bg-blue-900/90 backdrop-blur-md rounded-2xl px-5 py-3 shadow text-gray-800 dark:text-blue-100 border border-blue-200 dark:border-blue-800 relative">
                <p>${escapeHtml(text)}</p>
            </div>
        `;
        messageDiv.appendChild(innerDiv);
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
        
        // Determine selected documents
        let docs = window.selectedDocuments && window.selectedDocuments.length > 0 ? window.selectedDocuments : undefined;
        socket.emit('ask', { question, documents: docs });
        
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

