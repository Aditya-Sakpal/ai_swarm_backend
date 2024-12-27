from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from ..models import ConversationInput
from core import ConversationManager, AgentManager, DocumentGenerator

router = APIRouter()
agent_manager = AgentManager()

@router.post("/conversation/{agent_id}/chat")
async def chat(agent_id: str, conversation: ConversationInput):
    """
        This api endpoint is used to chat with an agent.
        
        Args :
            agent_id (str) : The id of the agent.
            conversation (ConversationInput) : The conversation details.
            
        Returns :
            List[Message] : The conversation messages.
    """
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    conv_manager = ConversationManager(agent)
    async def event_generator():
        """
            This function is a generator that yields the response
            messages from the agent.
            
            Yields :
                Dict : The response message.
        """
        response = conv_manager.get_response(conversation.messages)
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield {
                    "data": chunk.choices[0].delta.content
                }
    
    return EventSourceResponse(event_generator())

@router.post("/conversation/generate-document")
async def generate_document(conversation: ConversationInput):
    """
        This api endpoint is used to generate a document from the conversation. 
        
        Args :
            conversation (ConversationInput) : The conversation details.
            
        Returns :
            bytes : The generated document.
    """
    try:
        summary = DocumentGenerator.generate_summary(
            conversation.messages, 
            conversation.goal
        )
        doc_io = DocumentGenerator.create_document(
            summary, 
            conversation.goal, 
            conversation.messages
        )
        return doc_io
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))