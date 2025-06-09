# llm_rag.py

import json
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from langchain.chains import RetrievalQA, ConversationChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
# Import the translate_text function from the translations module in the same package
try:
    from src.translations import translate_text
except ImportError:
    # Fallback for local development
    from translations import translate_text

class ChatbotLLM:
    def __init__(self, vector_store, config_path="config.json"):
        """Initialize the Chatbot with a vector store and configuration.
        
        Args:
            vector_store: A FAISS vector store containing document embeddings
            config_path: Path to the configuration file
        """
        self.vector_store = vector_store
        self.config = self._load_config(config_path)
        self.llm = self._initialize_llm()
        
        # Initialize conversation memory before QA chain
        self.conversation_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Now initialize QA chain after memory is set up
        self.qa_chain = self._initialize_qa_chain()
        
        print("🤖 ChatbotLLM initialized with configuration:")
        print(f"   - Model: {self.config.get('llm_model_path', 'default')}")
        print(f"   - API Base: {self.config.get('llm_api_base', 'default')}")

    def _load_config(self, config_path):
        """Load configuration from JSON file."""
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found at {config_path}")
                
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Set default values for required configurations
            config.setdefault('llm_api_base', 'http://localhost:1234/v1')
            config.setdefault('llm_model_path', 'meta-llama-3.1-8b-instruct')
            config.setdefault('max_tokens', 1000)
            config.setdefault('temperature', 0.7)
            
            return config
            
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in config file: {config_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load config from {config_path}: {str(e)}")

    def _initialize_llm(self):
        """Initialize the language model with LM Studio."""
        try:
            # Configure environment variables for LM Studio
            os.environ["OPENAI_API_BASE"] = self.config["llm_api_base"]
            os.environ["OPENAI_API_KEY"] = "lm-studio"  # LM Studio doesn't require a real key
            
            print(f"🔌 Initializing LLM connection to {self.config['llm_api_base']}")
            
            # Return a ChatOpenAI instance configured for LM Studio
            return ChatOpenAI(
                model=self.config["llm_model_path"],
                temperature=float(self.config["temperature"]),
                max_tokens=int(self.config["max_tokens"]),
                streaming=False
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LLM: {str(e)}")

    def _initialize_qa_chain(self):
        """Initialize the QA chain with the vector store retriever."""
        if not self.vector_store:
            raise ValueError("Vector store is not initialized. Please process documents first.")

        try:
            # Custom prompt for RAG
            template = """You are an AI assistant that helps users find information in documents. 
            Use the following pieces of context to answer the question at the end. 
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            Keep the answer concise and to the point.
            
            Context:
            {context}
            
            Question: {question}
            Helpful Answer:"""

            prompt = PromptTemplate(
                template=template,
                input_variables=["context", "question"]
            )

            # Create a retriever from the vector store
            retriever = self.vector_store.as_retriever(
                search_kwargs={
                    "k": 4,  # Number of documents to retrieve
                    "score_threshold": 0.7  # Minimum similarity score
                }
            )

            # Create the QA chain
            return RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={
                    "prompt": prompt,
                    "memory": self.conversation_memory
                },
                verbose=True
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize QA chain: {str(e)}")

    async def ask_question(self, question: str, conversation_history: list = None) -> Dict[str, Any]:
        """Ask a question to the chatbot using the RAG pipeline.
        
        Args:
            question: The user's question
            conversation_history: List of previous messages in the conversation
            
        Returns:
            Dict containing the answer and source documents
            
        Example:
            {
                "answer": "The answer to your question...",
                "sources": [
                    {
                        "content": "Relevant text from document...",
                        "metadata": {"source": "document.pdf", "page": 1}
                    }
                ]
            }
        """
        if not question or not question.strip():
            return {
                "answer": "Please provide a valid question.",
                "sources": []
            }
            
        try:
            print(f"\n🤔 Question: {question}")
            
            # Add conversation history to the question if available
            if conversation_history:
                # Format the conversation history
                history_text = "\n".join(
                    f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                    for msg in conversation_history[-4:]  # Use last 4 messages for context
                )
                formatted_question = f"Previous conversation:\n{history_text}\n\nUser: {question}"
            else:
                formatted_question = question
                
            logger.debug(f"[DEBUG] Formatted question: {formatted_question}")

            # Get the answer
            try:
                # Ensure LLM is initialized
                if not hasattr(self, 'qa_chain') or self.qa_chain is None:
                    raise RuntimeError("QA chain is not initialized")
                    
                # Log the request
                logger.info(f"Sending request to LLM: {formatted_question[:200]}...")
                print("🔍 Searching for relevant information...")
                
                # Run the QA chain in a separate thread to avoid blocking
                import asyncio
                from functools import partial
                
                # Create a partial function with the QA chain call
                run_qa_chain = partial(self.qa_chain, {"query": formatted_question})
                
                # Run in a thread pool executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, run_qa_chain)
                
                # Process the result
                answer = result.get("result", "I couldn't find an answer to that question.")
                source_docs = result.get("source_documents", [])
                
                # Format the response
                response = {
                    "answer": answer.strip(),
                    "sources": [
                        {
                            "content": doc.page_content,
                            "metadata": dict(doc.metadata)
                        }
                        for doc in source_docs
                    ]
                }
                
                print(f"✅ Found {len(response['sources'])} relevant sources")
                return response
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                print(f"❌ Error: {error_msg}")
                import traceback
                traceback.print_exc()
                return {
                    "answer": error_msg,
                    "sources": []
                }
            
        except Exception as e:
            logger.error(f"[CRITICAL] Unhandled error in ask_question: {str(e)}", exc_info=True)
            return {
                "answer": "I encountered an unexpected error. The administrator has been notified.",
                "sources": []
            }

    async def process_message(self, message: str, conversation_id: str, user_id: str, language: str = 'en') -> Dict[str, Any]:
        """
        Process an incoming message and generate a response.
        
        Args:
            message: The user's message
            conversation_id: The ID of the conversation
            user_id: The ID of the user
            language: The preferred language for the response
            
        Returns:
            Dict containing the response and any additional data
        """
        try:
            print(f"Processing message: {message}")
            
            # Get the response from the QA chain
            response = await self.ask_question(message)
            
            # Generate smart suggestions based on the response
            suggestions = await self.get_smart_suggestions(
                message,
                response.get('answer', ''),
                language
            )
            
            # Format the response
            return {
                'response': response['answer'],
                'suggestions': suggestions[:3],  # Limit to 3 suggestions
                'sources': response.get('sources', [])
            }
            
        except Exception as e:
            print(f"Error in process_message: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'response': 'Sorry, I encountered an error processing your message. Please try again.',
                'suggestions': [],
                'sources': []
            }
    
    async def get_smart_suggestions(self, previous_question: str, context: str, language: str = 'en') -> List[str]:
        """
        Generate smart follow-up questions based on the previous question and context.
        
        Args:
            previous_question: The user's previous question
            context: The context or answer provided
            language: The preferred language for the suggestions
            
        Returns:
            List of suggested follow-up questions
        """
        try:
            # If no context is provided, return some generic suggestions
            if not context or not context.strip():
                return [
                    "Can you provide more details?",
                    "What specifically would you like to know?",
                    "Could you rephrase your question?"
                ]
                
            # Create a prompt for generating follow-up questions
            prompt = f"""Based on the following question and answer, generate 3 relevant follow-up questions.
            
            Question: {previous_question}
            Answer: {context}
            
            Generate 3 follow-up questions that would help clarify or expand on this information.
            Return them as a JSON array of strings, like: ["question 1", "question 2", "question 3"]
            """
            
            # Get the response from the LLM in a non-blocking way
            import asyncio
            from functools import partial
            
            # Create a partial function with the LLM call
            def call_llm():
                return self.llm.invoke(prompt)
                
            # Run in a thread pool executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, call_llm)
            
            # Parse the response
            try:
                # Extract content if it's an AIMessage
                if hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
                
                # Clean up the response (remove markdown code blocks if present)
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].strip()
                
                # Parse the JSON response
                import json
                suggestions = json.loads(response_text)
                if not isinstance(suggestions, list):
                    suggestions = [suggestions]
                
                # Ensure we have strings
                suggestions = [str(s) for s in suggestions if s and str(s).strip()]
                
                # If no valid suggestions, return defaults
                if not suggestions:
                    raise ValueError("No valid suggestions generated")
                
                # Translate to the target language if needed
                if language != 'en':
                    translated = []
                    for s in suggestions:
                        try:
                            # Run translation in the thread pool
                            translate_func = partial(translate_text, s, 'en', language)
                            translated_text = await loop.run_in_executor(None, translate_func)
                            translated.append(translated_text)
                        except Exception as e:
                            logger.warning(f"Failed to translate suggestion '{s}': {str(e)}")
                            translated.append(s)
                    return translated
                
                return suggestions
                
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Failed to parse LLM response as JSON: {str(e)}")
                # Fallback to a simple split if JSON parsing fails
                lines = [line.strip() for line in str(response).split('\n') if line.strip()]
                return lines[:3] if lines else [
                    "Can you clarify?", 
                    "Tell me more.", 
                    "What else would you like to know?"
                ]
                
        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}", exc_info=True)
            # Fallback to simple suggestions
            return [
                "Can you clarify?", 
                "Tell me more.", 
                "What else would you like to know?"
            ]

if __name__ == "__main__":
    import asyncio
    
    async def main():
        # This is a placeholder for testing. In a real scenario, you would pass a populated vector_store.
        # For demonstration, we'll create a dummy vector_store.
        from langchain_community.embeddings import SentenceTransformerEmbeddings
        from langchain_community.vectorstores import FAISS

        print("🔍 Creating dummy vector store...")
        # Create a dummy vector store
        texts = ["The quick brown fox jumps over the lazy dog.", 
                "Artificial intelligence is a rapidly developing field.",
                "The capital of France is Paris.",
                "Machine learning is a subset of artificial intelligence."]
        embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        dummy_vector_store = FAISS.from_texts(texts, embeddings)

        # Initialize ChatbotLLM with the dummy vector store
        print("🤖 Initializing ChatbotLLM...")
        chatbot = ChatbotLLM(dummy_vector_store)

        # Test with a simple question
        print("\n🧪 Testing with a simple question...")
        question = "What is AI?"
        answer = await chatbot.ask_question(question)
        print(f"\nQuestion: {question}")
        print(f"Answer: {answer['answer']}")
        
        # Test with a question that should retrieve from the vector store
        print("\n🧪 Testing with a question that should retrieve from the vector store...")
        question = "What is the capital of France?"
        answer = await chatbot.ask_question(question)
        print(f"\nQuestion: {question}")
        print(f"Answer: {answer['answer']}")
        
        # Test smart suggestions
        print("\n🧪 Testing smart suggestions...")
        suggestions = await chatbot.get_smart_suggestions(
            "What is AI?", 
            "AI, or Artificial Intelligence, refers to the simulation of human intelligence in machines."
        )
        print(f"\nSuggestions: {suggestions}")
    
    # Run the async main function
    asyncio.run(main())


