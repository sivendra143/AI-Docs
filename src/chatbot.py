"""
Chatbot module for handling conversation logic.
"""
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class Chatbot:
    """Main chatbot class for handling conversations."""
    
    def __init__(self):
        """Initialize the chatbot."""
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        logger.info("Chatbot initialized")
    
    async def process_message(self, message: str, conversation_id: str, **kwargs) -> Dict[str, Any]:
        """
        Process an incoming message and generate a response using the LLM.
        
        Args:
            message: The user's message
            conversation_id: Unique ID for the conversation
            **kwargs: Additional parameters
            
        Returns:
            Dict containing the response and metadata
        """
        logger.info(f"Processing message in conversation {conversation_id}: {message[:100]}...")
        
        # Initialize conversation if it doesn't exist
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        # Add user message to conversation history
        self.conversations[conversation_id].append({"role": "user", "content": message})
        
        try:
            # Get the ChatbotLLM instance from the app context
            from flask import current_app
            chatbot_llm = current_app.extensions.get('chatbot')
            
            if not chatbot_llm:
                raise RuntimeError("ChatbotLLM not initialized in app context. Available extensions: " + 
                                 ", ".join(current_app.extensions.keys()) if hasattr(current_app, 'extensions') else "No extensions found")
                
            # Get conversation history for context
            conversation_history = self.get_conversation_history(conversation_id)[-4:]  # Get last 4 messages
            
            # Generate response using the LLM (await if it's an async method)
            if hasattr(chatbot_llm, 'ask_question') and callable(chatbot_llm.ask_question):
                if hasattr(chatbot_llm.ask_question, '__await__'):
                    result = await chatbot_llm.ask_question(message, conversation_history)
                else:
                    result = chatbot_llm.ask_question(message, conversation_history)
            else:
                raise AttributeError("chatbot_llm.ask_question method not found")
            
            # Generate suggestions based on the response
            suggestions = []
            if hasattr(chatbot_llm, 'get_smart_suggestions') and callable(chatbot_llm.get_smart_suggestions):
                suggestions = chatbot_llm.get_smart_suggestions(
                    previous_question=message,
                    context=result.get("answer", ""),
                    language=kwargs.get("language", "en")
                )
            else:
                logger.warning("get_smart_suggestions method not found in chatbot_llm")
            
            # Format the response
            response = {
                "response": result.get("answer", "I'm sorry, I couldn't generate a response."),
                "conversation_id": conversation_id,
                "suggestions": suggestions[:3],  # Return up to 3 suggestions
                "sources": result.get("sources", []),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            response = {
                "response": "I'm sorry, I encountered an error while processing your message.",
                "conversation_id": conversation_id,
                "suggestions": ["Try again", "Ask something else"],
                "status": "error"
            }
        
        # Add bot response to conversation history
        self.conversations[conversation_id].append({"role": "assistant", "content": response["response"]})
        
        return response
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a given conversation ID.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            List of message dictionaries
        """
        return self.conversations.get(conversation_id, [])
    
    def end_conversation(self, conversation_id: str) -> bool:
        """
        End a conversation and clean up resources.
        
        Args:
            conversation_id: The ID of the conversation to end
            
        Returns:
            bool: True if conversation was ended, False if not found
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
