from pydantic import BaseModel
from typing import List, Optional

class AgentCreate(BaseModel):
    name: str
    role: str
    avatar: str
    expertise: List[str]
    personality: str

class AgentUpdate(AgentCreate):
    pass

class AgentResponse(AgentCreate):
    id: str
    has_knowledge_base: bool
    document_count: int

class Message(BaseModel):
    role: str
    content: str

class ConversationInput(BaseModel):
    messages: List[Message]
    goal: str

class GenerateSummaryRequest(BaseModel):
    messages: List[Message]

class CreateDocumentRequest(BaseModel):
    summary: str
    goal: str
    messages: List[Message]

class ProcessDocumentRequest(BaseModel):
    content: bytes
    filename: str

class ExtractTextFromPDFRequest(BaseModel):
    file_path: str

class AddDocumentRequest(BaseModel):
    content: bytes
    filename: str

class GetRelevantContextRequest(BaseModel):
    query: str
    k: Optional[int] = 3