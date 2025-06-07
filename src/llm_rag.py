# llm_rag.py

import json
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from langchain.chains import RetrievalQA, ConversationChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from translations import translate_text

class ChatbotLLM:
    def __init__(self, vector_store, config_path="config.json"):
        self.vector_store = vector_store
        self.config = self._load_config(config_path)
        self.llm = self._initialize_llm()
        self.qa_chain = self._initialize_qa_chain()

    def _load_config(self, config_path):
        with open(config_path, 'r') as f:
            return json.load(f)

    def _initialize_llm(self):
        # Set the OpenAI API base URL to point to LM Studio
        os.environ["OPENAI_API_BASE"] = self.config["llm_api_base"]
        # Use any non-empty string as the API key (LM Studio doesn't require a real key)
        os.environ["OPENAI_API_KEY"] = "lm-studio"
        
        # Create an OpenAI client
        client = OpenAI(
            base_url=self.config["llm_api_base"],
            api_key="lm-studio"
        )
        
        # Return a ChatOpenAI instance configured for LM Studio
        return ChatOpenAI(
            model=self.config["llm_model_path"],
            temperature=0.7,
            max_tokens=1000
        )

    def _initialize_qa_chain(self):
        if not self.vector_store:
            raise ValueError("Vector store is not initialized. Please process PDFs first.")

        # Custom prompt for RAG
        template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. Keep the answer as concise as possible.

{context}

Question: {question}
Helpful Answer:"""
        QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
        )
        return qa_chain

    def ask_question(self, question: str, language: str = 'en', conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[DEBUG] Starting ask_question with question: {question}")
        
        if not self.qa_chain:
            error_msg = "Error: Chatbot not initialized. Please process PDFs first."
            logger.error(error_msg)
            return error_msg

        try:
            logger.info("[DEBUG] Processing question translation...")
            # Translate non-English questions to English for better retrieval
            if language != 'en':
                translated_question = translate_text(question, 'en')
                logger.info(f"[DEBUG] Translated question to English: {translated_question}")
            else:
                translated_question = question
                logger.info("[DEBUG] No translation needed, using original question")

            # Add conversation history to context if available
            context = ""
            if conversation_history:
                logger.info(f"[DEBUG] Adding conversation history. Found {len(conversation_history)} messages")
                for msg in conversation_history[-5:]:  # Use last 5 messages as context
                    role = "User" if msg.get('is_user') else "Assistant"
                    context += f"{role}: {msg.get('content', '')}\n"
                logger.debug(f"[DEBUG] Context with history: {context}")
            else:
                logger.info("[DEBUG] No conversation history provided")

            # Format the question with context
            formatted_question = f"{context}\nQuestion: {translated_question}" if context else translated_question
            logger.debug(f"[DEBUG] Formatted question: {formatted_question}")

            logger.info("[DEBUG] Calling qa_chain...")
            # Get the answer with a timeout
            try:
                from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
                import functools
                
                # Define a wrapper function to run qa_chain with timeout
                def run_qa_chain():
                    return self.qa_chain({"query": formatted_question})
                
                # Run with timeout
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_qa_chain)
                    try:
                        result = future.result(timeout=30)  # 30 second timeout
                        logger.info("[DEBUG] Successfully got response from qa_chain")
                    except FutureTimeoutError:
                        logger.error("[ERROR] qa_chain timed out after 30 seconds")
                        return "I'm sorry, the request timed out. Please try again with a different question."
                    except Exception as e:
                        logger.error(f"[ERROR] Error in qa_chain: {str(e)}", exc_info=True)
                        return f"I encountered an error while processing your request: {str(e)}"
                
                answer = result.get("result", "")
                logger.info(f"[DEBUG] Raw answer from qa_chain: {answer[:100]}...")  # Log first 100 chars
                
                # Translate the answer back to the user's language if needed
                if language != 'en':
                    logger.info("[DEBUG] Translating answer...")
                    answer = translate_text(answer, language)
                    logger.debug(f"[DEBUG] Translated answer: {answer[:100]}...")

                # Fallback for out-of-scope queries
                if not answer or any(phrase in answer.lower() for phrase in ["don't know", "not covered", "no information"]):
                    logger.warning("[WARNING] No relevant information found for the question")
                    return "Sorry, I couldn't find relevant information in the documents to answer your question. Could you please rephrase or ask something else?"

                logger.info("[DEBUG] Successfully processed question")
                return answer
                
            except Exception as e:
                logger.error(f"[ERROR] Error in ask_question: {str(e)}", exc_info=True)
                return "I encountered an error while processing your request. Please try again later."
            
        except Exception as e:
            logger.error(f"[CRITICAL] Unhandled error in ask_question: {str(e)}", exc_info=True)
            return "I encountered an unexpected error. The administrator has been notified."

    def get_smart_suggestions(self, previous_question: str, context: str, language: str = 'en') -> List[str]:
        """
        Generate smart follow-up questions based on the previous question and context.
        
        Args:
            previous_question: The user's previous question
            context: The context or answer provided
            language: The preferred language for the suggestions
            
        Returns:
            List of suggested follow-up questions
        """
        suggestions = []
        
        # Simple rule-based suggestions
        if "how" in previous_question.lower():
            suggestions = [
                "Can you explain in more detail?",
                "What are the key points?",
                "Can you give me an example?"
            ]
        elif "what" in previous_question.lower():
            suggestions = [
                "What else should I know about this?",
                "How does this work?",
                "Can you provide more context?"
            ]
        else:
            suggestions = [
                "Tell me more about this topic.",
                "What are the main points?",
                "Can you explain in simpler terms?"
            ]
        
        # Translate suggestions if needed
        if language != 'en':
            suggestions = [translate_text(s, language) for s in suggestions]
            
        return suggestions[:3]  # Return max 3 suggestions

if __name__ == "__main__":
    # This is a placeholder for testing. In a real scenario, you would pass a populated vector_store.
    # For demonstration, we'll create a dummy vector_store.
    from langchain_community.embeddings import SentenceTransformerEmbeddings
    from langchain_community.vectorstores import FAISS

    # Create a dummy vector store
    texts = ["The quick brown fox jumps over the lazy dog.", "Artificial intelligence is a rapidly developing field."]
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    dummy_vector_store = FAISS.from_texts(texts, embeddings)

    # Initialize ChatbotLLM with the dummy vector store
    chatbot = ChatbotLLM(dummy_vector_store)

    # Example usage
    question = "What is AI?"
    answer = chatbot.ask_question(question)
    print(f"Question: {question}")
    print(f"Answer: {answer}")

    question = "What is the capital of France?"
    answer = chatbot.ask_question(question)
    print(f"Question: {question}")
    print(f"Answer: {answer}")

    suggestions = chatbot.get_smart_suggestions("What is AI?", "Some context about AI.")
    print(f"Suggestions: {suggestions}")


