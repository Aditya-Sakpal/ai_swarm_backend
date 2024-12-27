from fastapi import APIRouter, HTTPException

from core.document_generator import DocumentGenerator
from core.document_processor import DocumentProcessor
from api.models import (  
    GenerateSummaryRequest,
    CreateDocumentRequest,
    ProcessDocumentRequest,
    ExtractTextFromPDFRequest,
    AddDocumentRequest,
    GetRelevantContextRequest,
)

document_generator = DocumentGenerator()

router = APIRouter()

@router.post("/generate_summary")
async def generate_summary(request: GenerateSummaryRequest):
    """
        This api endpoint is used to generate a summary from the conversation. 
        
        Args :
            request (GenerateSummaryRequest) : The request details.
            
        Returns :
            str : The generated summary.
    """
    try:
        return document_generator.generate_summary(request.messages)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create_document")
async def create_document(request: CreateDocumentRequest):
    """
        This api endpoint is used to create a document from the conversation.
        
        Args :
            request (CreateDocumentRequest) : The request details.
            
        Returns :
            bytes : The generated document.
    """
    try:
        doc_io = document_generator.create_document(request.summary, request.goal, request.messages)
        return doc_io
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/process_document/{agent_id}")
async def process_document(agent_id: str, request: ProcessDocumentRequest):
    """
        This api endpoint is used to process a document.
        
        Args :
            agent_id (str) : The id of the agent.
            request (ProcessDocumentRequest) : The request details.
            
        Returns :
            Dict : The processed document details.
    """
    try:
        document_processor = DocumentProcessor(agent_id)
        return document_processor.process_document(request.content, request.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/extract_text_from_pdf/{agent_id}")
async def extract_text_from_pdf(agent_id: str, request: ExtractTextFromPDFRequest):
    """
        This api endpoint is used to extract text from a pdf.
        
        Args :
            agent_id (str) : The id of the agent.
            request (ExtractTextFromPDFRequest) : The request details.
            
        Returns :
            str : The extracted text.
    """
    try:
        document_processor = DocumentProcessor(agent_id)
        return document_processor._extract_text_from_pdf(request.file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/add_document/{agent_id}")
async def add_document(agent_id: str, request: AddDocumentRequest):
    """
        This api endpoint is used to add a document to the agent's knowledge base.
        
        Args :
            agent_id (str) : The id of the agent.
            request (AddDocumentRequest) : The request details.
            
        Returns :
            Tuple[bool, str] : The result of the operation.
    """
    try:
        document_processor = DocumentProcessor(agent_id)
        return document_processor.add_document(request.content, request.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/get_relevant_context/{agent_id}")
async def get_relevant_context(agent_id: str, request: GetRelevantContextRequest):
    """
        This api endpoint is used to get the relevant context for a query.
        
        Args :
            agent_id (str) : The id of the agent.
            request (GetRelevantContextRequest) : The request details.
            
        Returns :
            List[str] : The relevant context.
    """
    try:
        document_processor = DocumentProcessor(agent_id)
        return document_processor.get_relevant_context(request.query, request.k)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))