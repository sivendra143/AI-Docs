import requests
from src.config import DevelopmentConfig
from src.services import pdf_rag

def get_chat_response(user_message):
    """Get response from the AI model, with PDF RAG context."""
    try:
        # Retrieve relevant context from PDFs
        context_chunks = pdf_rag.retrieve_context(user_message, k=4)
        context_text = "\n\n".join(context_chunks)
        print(f"[DEBUG] Retrieved context chunks: {context_chunks}")
        if context_text:
            augmented_message = f"You are a PDF assistant. Use the following context from the user's documents to answer the question.\n\nContext:\n{context_text}\n\nQuestion: {user_message}"
        else:
            augmented_message = user_message
        print(f"[DEBUG] Sending to LM Studio: {augmented_message}")
        payload = {
            'model': 'meta-llama-3.1-8b-instruct',
            'messages': [{'role': 'user', 'content': augmented_message}]
        }
        print(f"[DEBUG] Payload: {payload}")
        response = requests.post(
            'http://localhost:1234/v1/chat/completions',
            json=payload,
            timeout=30
        )
        print(f"[DEBUG] HTTP status: {response.status_code}")
        print(f"[DEBUG] Raw response: {response.text}")
        response.raise_for_status()
        answer = response.json()['choices'][0]['message']['content']
        print(f"[DEBUG] Answer: {answer}")
        return answer
    except Exception as e:
        print(f"[ERROR] Error getting chat response: {str(e)}")
        return "I'm sorry, I encountered an error processing your request."

class Chatbot:
    def ask_question(self, question, language=None, conversation_history=None):
        return get_chat_response(question)
