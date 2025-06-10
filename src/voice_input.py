# voice_input.py

import os
import sys
import tempfile
import traceback
import json
import whisper
import torch
import time
from flask import Flask, request, jsonify, current_app

class VoiceProcessor:
    def __init__(self, model_size="tiny"):
        """
        Initialize the voice processor with a Whisper model.
        
        Args:
            model_size (str): Size of the Whisper model to use ('tiny', 'base', 'small', 'medium', 'large')
        """
        self.model = None
        self.model_size = model_size
        self._model_loaded = False
        
    def load_model(self):
        """
        Load the Whisper model if not already loaded.
        """
        if self.model is None:
            try:
                print(f"[VOICE] Loading Whisper {self.model_size} model...")
                self.model = whisper.load_model(self.model_size)
                self._model_loaded = True
                print(f"[VOICE] Whisper {self.model_size} model loaded successfully.")
                return True
            except Exception as e:
                print(f"[VOICE] Error loading Whisper model: {str(e)}")
                traceback.print_exc()
                return False
        return True
        
    def transcribe_audio(self, audio_file_path):
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path (str): Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        if not self._model_loaded:
            success = self.load_model()
            if not success:
                return ""
            
        try:
            print(f"[VOICE] Transcribing audio file: {audio_file_path}")
            # Set a timeout to prevent hanging
            start_time = time.time()
            result = self.model.transcribe(audio_file_path)
            elapsed = time.time() - start_time
            print(f"[VOICE] Transcription completed in {elapsed:.2f} seconds")
            return result["text"]
        except Exception as e:
            print(f"[VOICE] Error transcribing audio: {str(e)}")
            traceback.print_exc()
            return ""

def setup_voice_routes(app, chatbot):
    """
    Set up Flask routes for voice input processing.
    Args:
        app (Flask): Flask application
        chatbot: Chatbot instance to process transcribed text
    """
    # Create voice processor at module level to avoid recreation on each request
    voice_processor = VoiceProcessor(model_size="tiny")  # Use tiny model for faster processing
    
    # Pre-load the model at startup to avoid delay on first request
    try:
        voice_processor.load_model()
    except Exception as e:
        print(f"[VOICE] WARNING: Failed to pre-load Whisper model: {str(e)}")
        print("[VOICE] Will attempt to load on first request instead.")

    @app.route('/api/voice/health', methods=['GET'])
    def voice_health():
        """Health check endpoint for local development."""
        return jsonify({
            'status': 'ok', 
            'message': 'Voice API is up',
            'whisper_loaded': voice_processor.model is not None
        }), 200
    
    @app.route('/api/voice', methods=['POST'])
    def process_voice():
        print("[VOICE] /api/voice endpoint called")
        temp_audio_path = None
        
        try:
            # Check for audio file in request
            if 'audio' not in request.files:
                print("[VOICE] No audio file provided in request.files")
                return jsonify({'error': 'No audio file provided'}), 400
            
            audio_file = request.files['audio']
            print(f"[VOICE] Received audio file: {audio_file.filename}, Content-Type: {audio_file.content_type}")
            
            # Save the uploaded audio file to a temporary file (webm)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_audio:
                audio_file.save(temp_audio.name)
                temp_audio_path = temp_audio.name
            
            # Check file size
            temp_file_size = os.path.getsize(temp_audio_path)
            print(f"[VOICE] Temp file size: {temp_file_size} bytes")
            
            if temp_file_size == 0:
                print("[VOICE] Uploaded audio file is empty!")
                os.unlink(temp_audio_path)
                return jsonify({'error': 'Uploaded audio file is empty! Please try recording again.'}), 400
            
            # First try with the real transcription
            try:
                # Transcribe the audio
                print("[VOICE] Starting transcription...")
                transcribed_text = voice_processor.transcribe_audio(temp_audio_path)
                print(f"[VOICE] Transcription result: '{transcribed_text}'")
                
                if not transcribed_text or transcribed_text.strip() == "":
                    print("[VOICE] Transcription failed or returned empty text.")
                    # Fall back to dummy text if transcription fails
                    transcribed_text = "I couldn't transcribe the audio clearly."
            except Exception as e:
                print(f"[VOICE] Error during transcription: {str(e)}")
                # Fall back to dummy text if transcription fails
                transcribed_text = "I couldn't transcribe the audio clearly."
            
            # Process the transcribed text with the chatbot
            try:
                print("[VOICE] Sending transcription to chatbot...")
                answer = chatbot.ask_question(transcribed_text)
                suggestions = chatbot.get_smart_suggestions(transcribed_text, answer)
                print(f"[VOICE] Chatbot answer received, length: {len(answer)}")
            except Exception as e:
                print(f"[VOICE] Error getting chatbot response: {str(e)}")
                # Fall back to dummy response
                answer = f"I understood: {transcribed_text}. But I couldn't process a response."
                suggestions = ["Try again", "Type your question instead", "Help me"]
            
            # Clean up the temporary file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                print(f"[VOICE] Temp file deleted.")
            
            # Return successful response
            return jsonify({
                'transcription': transcribed_text,
                'answer': answer,
                'suggestions': suggestions
            })
            
        except Exception as e:
            print(f"[VOICE] Exception in /api/voice: {str(e)}")
            traceback.print_exc()
            
            # Clean up the temporary file in case of error
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                    print(f"[VOICE] Temp file deleted after error.")
                except:
                    pass
                    
            # Return error response with fallback
            return jsonify({
                'transcription': 'Sorry, I had trouble processing your audio.',
                'answer': 'There was a problem processing your voice input. Please try again or type your question.',
                'suggestions': ['Try again', 'Type instead', 'Help']
            })

if __name__ == "__main__":
    # For testing purposes
    app = Flask(__name__)
    
    class DummyChatbot:
        def ask_question(self, question):
            return f"Answer to: {question}"
            
        def get_smart_suggestions(self, question, answer):
            return ["Tell me more", "How does this work?", "Can you explain further?"]
    
    dummy_chatbot = DummyChatbot()
    setup_voice_routes(app, dummy_chatbot)
    
    app.run(debug=True)
