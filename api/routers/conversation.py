from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from ..models import ConversationInput , GenerateDocumentInput
from core import ConversationManager, AgentManager, DocumentGenerator
import traceback

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
    
    messages = []
    for message in conversation.messages:
        if message.agent_id != agent_id:
            messages.append({
                "role": "user",
                "content": message.content
            })
        else:
            messages.append({
                "role": "assistant",
                "content": message.content
            })
    
    conv_manager = ConversationManager(agent)
    async def event_generator():
        """
            This function is a generator that yields the response
            messages from the agent.
            
            Yields :
                Dict : The response message.
        """
        response = conv_manager.get_response(messages)
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield {
                    "data": chunk.choices[0].delta.content
                }
    
    return EventSourceResponse(event_generator())

@router.post("/conversation/generate-document")
async def generate_document(conversation: GenerateDocumentInput):
    """
        This api endpoint is used to generate a document from the conversation. 
        
        Args :
            conversation (ConversationInput) : The conversation details.
            
        Returns :
            bytes : The generated document.
    """
    try:
        
        summary = DocumentGenerator.generate_summary(
            conversation.messages
        )
        doc_io = DocumentGenerator.create_document(
            summary, 
            conversation.goal, 
            conversation.messages
        )
        return doc_io
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))