// voice.js - Voice input functionality

let mediaRecorder;
let audioChunks = [];
let isRecording = false; // Ensure mediaRecorder is declared only once in the file

document.addEventListener('DOMContentLoaded', function() {
    const startRecordingBtn = document.getElementById('start-recording');
    const stopRecordingBtn = document.getElementById('stop-recording');
    const recordingStatus = document.getElementById('recording-status');
    
    if (!startRecordingBtn || !stopRecordingBtn) return;
    
    // Check if browser supports getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        startRecordingBtn.disabled = true;
        recordingStatus.textContent = 'Voice recording not supported in this browser';
        return;
    }
    
    startRecordingBtn.addEventListener('click', startRecording);
    stopRecordingBtn.addEventListener('click', stopRecording);
});

async function startRecording() {
    if (isRecording) return;
    
    const startRecordingBtn = document.getElementById('start-recording');
    const stopRecordingBtn = document.getElementById('stop-recording');
    const recordingStatus = document.getElementById('recording-status');
    
    audioChunks = [];
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.addEventListener('dataavailable', event => {
            audioChunks.push(event.data);
        });
        
        mediaRecorder.addEventListener('stop', processRecording);
        
        mediaRecorder.start();
        isRecording = true;
        
        startRecordingBtn.disabled = true;
        stopRecordingBtn.disabled = false;
        startRecordingBtn.classList.add('hidden');
        stopRecordingBtn.classList.remove('hidden');
        recordingStatus.textContent = 'Recording...';
        recordingStatus.classList.add('recording');
        
        // Pulse animation for recording indicator
        startPulseAnimation();
        
    } catch (error) {
        console.error('Error starting recording:', error);
        recordingStatus.textContent = 'Error: Could not access microphone';
    }
}

function stopRecording() {
    if (!isRecording || !mediaRecorder) return;
    
    mediaRecorder.stop();
    isRecording = false;
    
    const startRecordingBtn = document.getElementById('start-recording');
    const stopRecordingBtn = document.getElementById('stop-recording');
    const recordingStatus = document.getElementById('recording-status');
    
    startRecordingBtn.disabled = false;
    stopRecordingBtn.disabled = true;
    startRecordingBtn.classList.remove('hidden');
    stopRecordingBtn.classList.add('hidden');
    recordingStatus.textContent = 'Processing...';
    recordingStatus.classList.remove('recording');
    
    // Stop pulse animation
    stopPulseAnimation();
    
    // Stop all audio tracks
    mediaRecorder.stream.getTracks().forEach(track => track.stop());
}

async function processRecording() {
    const recordingStatus = document.getElementById('recording-status');
    
    if (audioChunks.length === 0) {
        recordingStatus.textContent = 'No audio recorded';
        return;
    }
    
    recordingStatus.textContent = 'Transcribing...';
    console.log('Processing audio recording, chunks:', audioChunks.length);
    
    // Create audio blob and send to server
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    
    // Add conversation ID if available
    if (window.chatApp && window.chatApp.currentConversationId) {
        formData.append('conversation_id', window.chatApp.currentConversationId);
        console.log('Added conversation ID to voice request:', window.chatApp.currentConversationId);
    }
    
    try {
        console.log('Sending voice data to server...');
        const response = await fetch('/api/voice', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            console.error('Server error response:', response.status, response.statusText);
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Voice API response received:', data);
        
        // Add user message with transcription
        if (window.chatApp && typeof window.chatApp.addUserMessage === 'function') {
            window.chatApp.addUserMessage(data.transcription);
            console.log('Added user transcription to chat:', data.transcription);
        } else {
            console.error('Could not add user message - chatApp not available');
        }
        
        // Add bot response
        if (window.chatApp && typeof window.chatApp.addBotMessage === 'function' && data.answer) {
            window.chatApp.addBotMessage(data.answer);
            console.log('Added bot response to chat');
        }
        
        // Display suggestions
        if (window.chatApp && typeof window.chatApp.displaySuggestions === 'function' && 
            data.suggestions && Array.isArray(data.suggestions)) {
            window.chatApp.displaySuggestions(data.suggestions);
            console.log('Displayed suggestions:', data.suggestions);
        }
        
        recordingStatus.textContent = '';
        
    } catch (error) {
        console.error('Error processing audio:', error);
        recordingStatus.textContent = 'Error processing audio';
        
        // Show error message in chat for user feedback
        if (window.chatApp && typeof window.chatApp.addSystemMessage === 'function') {
            window.chatApp.addSystemMessage(`Voice recording error: ${error.message}`);
        }
        
        // Enable the start recording button again
        const startRecordingBtn = document.getElementById('start-recording');
        if (startRecordingBtn) {
            startRecordingBtn.disabled = false;
            startRecordingBtn.classList.remove('hidden');
        }
    }
}

// Visual feedback for recording
function startPulseAnimation() {
    const micIcon = document.querySelector('.mic-icon');
    if (micIcon) {
        micIcon.classList.add('pulsing');
    }
}

function stopPulseAnimation() {
    const micIcon = document.querySelector('.mic-icon');
    if (micIcon) {
        micIcon.classList.remove('pulsing');
    }
}

