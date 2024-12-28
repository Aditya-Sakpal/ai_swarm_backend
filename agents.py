import openai
import streamlit as st
from typing import List, Dict, Optional
from document_processor import AgentDocumentProcessor

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
            "You are part of a research panel focused on achieving a well-supported conclusion. Your responsibilities include:\n"
            "1. Presenting your viewpoint with clear, evidence-based arguments.\n"
            "2. Critically evaluating and responding to counterarguments from other panel members.\n"
            "3. Collaboratively working towards a consensus or clearly articulated disagreements.\n"
            "Ensure that all contributions are concise, straight to the point, and grounded in facts.\n"
            "Additional Knowledge Base Context:\n"
            "The following information from the agent's knowledge base may be relevant. "
            "Incorporate this information naturally into your responses when appropriate:\n"
            f"{context}"
        )
        
        return enhanced_message
    
    def get_response(self, messages: List[Dict[str, str]]) -> Optional[openai.ChatCompletion]:
        """
        Generate a response incorporating knowledge base context when relevant.
        
        Args:
            messages (List[Dict[str, str]]): Conversation history
            
        Returns:
            Optional[openai.ChatCompletion]: Streamed response or None if error occurs
        """
        try:
            # Get context for the last message if available
            context = ""
            if messages:
                last_message = messages[-1]["content"]
                context = self.get_relevant_context(last_message)
            
            # Enhance system message with context
            system_message = self.enhance_system_message(self.personality, context)
            
            # Create messages with enhanced context
            messages_with_context = [
                {"role": "system", "content": system_message}
            ] + messages
            
            # Generate response
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages_with_context,
                temperature=0.7,
                max_tokens=800,
                stream=True
            )
            
            return response
            
        except Exception as e:
            st.error(f"Error getting response: {str(e)}")
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