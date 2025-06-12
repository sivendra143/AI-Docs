// chat-simple.js - Simplified chat functionality

document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const questionForm = document.getElementById('question-form');
    const questionInput = document.getElementById('question-input');
    let isProcessing = false;

    // Add a message to the chat
    function addMessage(text, sender = 'bot') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Show loading indicator
    function showLoading(show = true) {
        const loading = document.getElementById('loading-indicator');
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
        }
    }

    // Handle form submission
    async function handleSubmit(e) {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question || isProcessing) return;
        
        isProcessing = true;
        questionInput.value = '';
        addMessage(question, 'user');
        showLoading(true);
        
        try {
            // Use the test endpoint
            const response = await fetch('/api/test/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                addMessage(data.response, 'bot');
            } else {
                addMessage('Error: ' + (data.error || 'Unknown error occurred'), 'system');
            }
        } catch (error) {
            console.error('Error:', error);
            addMessage('Error: Could not connect to the server', 'system');
        } finally {
            isProcessing = false;
            showLoading(false);
        }
    }

    // Add event listeners
    if (questionForm) {
        questionForm.addEventListener('submit', handleSubmit);
    }

    // Default greeting to show the user the system is working
    addMessage('Hello! How can I help you today?', 'bot');
});
