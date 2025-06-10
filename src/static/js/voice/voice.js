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
    
    // Create audio blob and send to server
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    
    try {
        const response = await fetch('/api/voice', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Server error');
        }
        
        const data = await response.json();
        
        // Add user message with transcription
        addUserMessage(data.transcription);
        
        // Add bot response
        addBotMessage(data.answer);
        
        // Display suggestions
        displaySuggestions(data.suggestions);
        
        recordingStatus.textContent = '';
        
    } catch (error) {
        console.error('Error processing audio:', error);
        recordingStatus.textContent = 'Error processing audio';
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

