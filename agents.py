import openai
import streamlit as st
import traceback
from typing import List, Dict, Optional
from document_processor import AgentDocumentProcessor
from redis_client import redis_client

class ConversationAgent:
    def __init__(self, 
                 name: str, 
                 role: str, 
                 personality: str, 
                 agent_id: Optional[str] = None,
                 expertise: Optional[List[str]] = None):
        """
        Initialize a conversation agent with optional knowledge base integration.
        
        Args:
            name (str): Name of the agent
            role (str): Role of the agent ("user" or "assistant")
            personality (str): Personality description/prompt for the agent
            agent_id (Optional[str]): ID for knowledge base lookup
            expertise (Optional[List[str]]): List of expertise areas
        """
        self.name = name
        self.role = role
        self.personality = personality
        self.agent_id = agent_id
        self.expertise = expertise or []
        
        # Initialize document processor if agent_id is provided
        self.doc_processor = None
        if agent_id:
            try:
                self.doc_processor = AgentDocumentProcessor(
                    agent_id=agent_id,
                    openai_api_key=openai.api_key
                )
            except Exception as e:
                print(f"Error initializing document processor: {e}")
    
    def get_relevant_context(self, query: str) -> str:
        """
        Retrieve relevant context from the agent's knowledge base.
        
        Args:
            query (str): The query to find relevant context for
            
        Returns:
            str: Relevant context from documents or empty string if none found
        """
        if not self.doc_processor:
            return ""
        
        try:
            relevant_docs = self.doc_processor.get_relevant_context(query)
            if relevant_docs:
                return "\n\nRelevant information from knowledge base:\n" + "\n".join(relevant_docs)
        except Exception as e:
            print(f"Error retrieving context: {str(e)}")
        
        return ""
    
    def enhance_system_message(self, base_personality: str, context: str) -> str:
        """
        Combine personality with relevant context for a complete system message.
        
        Args:
            base_personality (str): The base personality prompt
            context (str): Relevant context from knowledge base
            
        Returns:
            str: Enhanced system message
        """
        if not context:
            return base_personality
        
        # Add context integration instructions
        enhanced_message = (
            f"{base_personality}\n\n"
            "Additional Knowledge Base Context:\n"
            "The following information from the agent's knowledge base may be relevant. "
            "Incorporate this information naturally into your responses when appropriate:\n"
            f"{context}"
        )
        
        return enhanced_message

    def store_message_in_cache(self, conversation_id: str, message: Dict[str, str]):
        """
        Store the message in the cache.
        
        Args:
            conversation_id (str): The conversation id.
            message (Dict[str, str]): The message.
            
        Returns:
            None
        """
        redis_key = f"conversation:{conversation_id}:messages"
        print(message)
        redis_client.rpush(redis_key, message)
        redis_client.ltrim(redis_key, -3, -1)
        
    def get_cached_messages(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Retrieve the last three messages from Redis for the given conversation ID.
        """
        redis_key = f"conversation:{conversation_id}:messages"
        cached_messages = redis_client.lrange(redis_key, 0, -1)
        print(cached_messages)
        return [eval(msg) for msg in cached_messages] 
    
    def get_response(self, messages: List[Dict[str, str]], conversation_id: str) -> Optional[openai.ChatCompletion]:
        """
        Generate a response incorporating knowledge base context when relevant.

        Args:
            messages (List[Dict[str, str]]): Conversation history
            conversation_id (str): Unique conversation identifier
            
        Returns:
            Optional[openai.ChatCompletion]: Streamed response or None if error occurs
        """
        try:
            # Store the last message in the Redis cache
            if messages:
                for message in messages:
                    self.store_message_in_cache(conversation_id, message)

            # Retrieve cached messages
            cached_messages = self.get_cached_messages(conversation_id)

            # Get context for the last message if available
            context = ""
            if cached_messages:
                last_message = cached_messages[-1]["content"]
                context = self.get_relevant_context(last_message)

            # Enhance system message with context
            system_message = self.enhance_system_message(self.personality, context)

            # Create messages with enhanced context
            messages_with_context = [{"role": "system", "content": system_message}] + cached_messages
            
            print(messages_with_context)

            # Generate response
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages_with_context,
                temperature=0.9,
                max_tokens=800,
                stream=True
            )

            return response

        except Exception as e:
            print(f"Error generating response: {traceback.format_exc()}")
            return None
    
    def add_document_to_knowledge_base(self, document) -> tuple[bool, str]:
        """
        Add a new document to the agent's knowledge base.
        
        Args:
            document: The document to add (file object)
            
        Returns:
            tuple[bool, str]: Success status and message
        """
        if not self.doc_processor:
            return False, "No document processor initialized"
        
        try:
            return self.doc_processor.add_document(document)
        except Exception as e:
            return False, f"Error adding document: {str(e)}"