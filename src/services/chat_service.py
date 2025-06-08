import requests
from config import Development

def get_chat_response(user_message):
    """Get response from the AI model"""
    try:
        # Call LM Studio API
        response = requests.post(
            'http://localhost:1234/v1/chat/completions',
            json={
                'model': 'meta-llama-3.1-8b-instruct',
                'messages': [{'role': 'user', 'content': user_message}]
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
        
    except Exception as e:
        print(f"Error getting chat response: {str(e)}")
        return "I'm sorry, I encountered an error processing your request."
