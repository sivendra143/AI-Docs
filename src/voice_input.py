# voice_input.py

import os
import tempfile
import json
import whisper
from flask import Flask, request, jsonify

class VoiceProcessor:
    def __init__(self, model_size="base"):
        """
        Initialize the voice processor with a Whisper model.
        
        Args:
            model_size (str): Size of the Whisper model to use ('tiny', 'base', 'small', 'medium', 'large')
        """
        self.model = None
        self.model_size = model_size
        
    def load_model(self):
        """
        Load the Whisper model if not already loaded.
        """
        if self.model is None:
            print(f"Loading Whisper {self.model_size} model...")
            self.model = whisper.load_model(self.model_size)
            print("Whisper model loaded.")
        
    def transcribe_audio(self, audio_file_path):
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path (str): Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        if self.model is None:
            self.load_model()
            
        try:
            result = self.model.transcribe(audio_file_path)
            return result["text"]
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return ""

def setup_voice_routes(app, chatbot):
    """
    Set up Flask routes for voice input processing.
    
    Args:
        app (Flask): Flask application
        chatbot: Chatbot instance to process transcribed text
    """
    voice_processor = VoiceProcessor()
    
    @app.route('/api/voice', methods=['POST'])
    def process_voice():
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio']
        
        # Save the uploaded audio file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            audio_file.save(temp_audio.name)
            temp_audio_path = temp_audio.name
            
        try:
            # Transcribe the audio
            transcribed_text = voice_processor.transcribe_audio(temp_audio_path)
            
            if not transcribed_text:
                return jsonify({'error': 'Failed to transcribe audio'}), 500
                
            # Process the transcribed text with the chatbot
            answer = chatbot.ask_question(transcribed_text)
            suggestions = chatbot.get_smart_suggestions(transcribed_text, answer)
            
            # Clean up the temporary file
            os.unlink(temp_audio_path)
            
            return jsonify({
                'transcription': transcribed_text,
                'answer': answer,
                'suggestions': suggestions
            })
            
        except Exception as e:
            # Clean up the temporary file in case of error
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            return jsonify({'error': str(e)}), 500

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

