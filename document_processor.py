import os
from typing import List, Dict
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
import hashlib
from tqdm import tqdm
import chromadb
import tempfile
import streamlit as st

class AgentDocumentProcessor:
    def __init__(self, agent_id: str, openai_api_key: str):
        """
            This constructor initializes the agent document processor.
            
            Args :
                agent_id (str) : The id of the agent.
                openai_api_key (str) : The OpenAI API key.
                
            Returns :
                None
        """
        self.agent_id = agent_id
        self.openai_api_key = openai_api_key
        
        # Create a unique persistent directory for each agent's ChromaDB
        self.db_path = f"agent_knowledge/{agent_id}"
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize ChromaDB for this agent
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name=f"agent_{agent_id}_knowledge"
        )
        
        # Initialize embeddings and text splitter
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def process_file(self, uploaded_file) -> Dict[str, List[str]]:
        """
            This function processes an uploaded file.
            
            Args :
                uploaded_file : The uploaded file.
                
            Returns :
                Dict[str, List[str]] : The processed file details.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            file_path = tmp_file.name

        try:
            if uploaded_file.name.lower().endswith('.pdf'):
                text = self._extract_text_from_pdf(file_path)
            else:  # txt file
                text = uploaded_file.getvalue().decode('utf-8')

            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Generate unique IDs for chunks
            ids = [
                hashlib.md5(f"{uploaded_file.name}_{i}".encode()).hexdigest() 
                for i in range(len(chunks))
            ]
            
            # Prepare metadata
            metadatas = [{
                "source": uploaded_file.name,
                "chunk_index": i,
                "total_chunks": len(chunks)
            } for i in range(len(chunks))]

            # Clean up temp file
            os.unlink(file_path)
            
            return {
                "ids": ids,
                "chunks": chunks,
                "metadatas": metadatas
            }

        except Exception as e:
            if os.path.exists(file_path):
                os.unlink(file_path)
            raise e

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """
            This function extracts text from a PDF file.
            
            Args :
                file_path (str) : The path to the PDF file.
                
            Returns :
                str : The extracted text.
        """
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text

    def add_document(self, uploaded_file):
        """
            This function adds a document to the agent's knowledge base.
            
            Args :
                uploaded_file : The uploaded file.
                
            Returns :
                Tuple[bool, str] : The result of the operation
        """
        try:
            doc_data = self.process_file(uploaded_file)
            
            # Generate embeddings
            embeddings = self.embeddings.embed_documents(doc_data["chunks"])
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=doc_data["chunks"],
                ids=doc_data["ids"],
                metadatas=doc_data["metadatas"]
            )
            
            return True, f"Successfully processed: {uploaded_file.name}"
            
        except Exception as e:
            return False, f"Error processing {uploaded_file.name}: {str(e)}"

    def get_relevant_context(self, query: str, k: int = 3) -> List[str]:
        """
            This function gets the relevant context for a query.
            
            Args :
                query (str) : The query.
                k (int) : The number of results to return.
                
            Returns :
                List[str] : The relevant context.
        """
        query_embedding = self.embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        return results.get("documents", [[]])[0]