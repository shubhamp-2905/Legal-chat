import os
import json
import logging
from typing import List, Dict, Any
from pathlib import Path
import hashlib
import re

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader, 
    PyPDFLoader, 
    DirectoryLoader
)
from langchain.schema import Document
import docx2txt

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDocumentLoader:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
    def load_txt_file(self, file_path: str) -> List[Document]:
        """Load and process text files"""
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            return self._add_metadata(documents, file_path)
        except Exception as e:
            logger.error(f"Error loading text file {file_path}: {e}")
            return []
    
    def load_pdf_file(self, file_path: str) -> List[Document]:
        """Load and process PDF files"""
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            return self._add_metadata(documents, file_path)
        except Exception as e:
            logger.error(f"Error loading PDF file {file_path}: {e}")
            return []
    
    def load_docx_file(self, file_path: str) -> List[Document]:
        """Load and process DOCX files"""
        try:
            text = docx2txt.process(file_path)
            doc = Document(page_content=text)
            return self._add_metadata([doc], file_path)
        except Exception as e:
            logger.error(f"Error loading DOCX file {file_path}: {e}")
            return []
    
    def _add_metadata(self, documents: List[Document], file_path: str) -> List[Document]:
        """Add metadata to documents"""
        filename = os.path.basename(file_path)
        file_type = filename.split('.')[-1].lower()
        
        for doc in documents:
            doc.metadata.update({
                'source': filename,
                'file_path': file_path,
                'file_type': file_type,
                'doc_id': self._generate_doc_id(doc.page_content)
            })
        return documents
    
    def _generate_doc_id(self, content: str) -> str:
        """Generate unique document ID"""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep legal formatting
        text = re.sub(r'[^\w\s\.\,\;\:\(\)\-\[\]\"\'\/]', '', text)
        # Normalize case for certain legal terms
        text = self._normalize_legal_terms(text)
        return text.strip()
    
    def _normalize_legal_terms(self, text: str) -> str:
        """Normalize common legal terms"""
        legal_terms = {
            'indian penal code': 'IPC',
            'code of criminal procedure': 'CrPC',
            'code of civil procedure': 'CPC',
            'constitution of india': 'Constitution',
        }
        
        for term, normalized in legal_terms.items():
            text = re.sub(term, normalized, text, flags=re.IGNORECASE)
        return text
    
    def load_all_documents(self, folder_path: str = None) -> List[Document]:
        """Load all documents from the specified folder"""
        if folder_path is None:
            folder_path = settings.LEGAL_DOCS_PATH
            
        if not os.path.exists(folder_path):
            logger.error(f"Document folder not found: {folder_path}")
            return []
        
        all_documents = []
        supported_extensions = {'.txt', '.pdf', '.docx'}
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                if file_ext in supported_extensions:
                    logger.info(f"Loading: {file}")
                    
                    if file_ext == '.txt':
                        docs = self.load_txt_file(file_path)
                    elif file_ext == '.pdf':
                        docs = self.load_pdf_file(file_path)
                    elif file_ext == '.docx':
                        docs = self.load_docx_file(file_path)
                    
                    # Preprocess content
                    for doc in docs:
                        doc.page_content = self.preprocess_text(doc.page_content)
                    
                    all_documents.extend(docs)
        
        logger.info(f"Loaded {len(all_documents)} documents")
        return all_documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks"""
        chunks = self.text_splitter.split_documents(documents)
        
        # Add chunk-specific metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                'chunk_id': f"chunk_{i}",
                'chunk_size': len(chunk.page_content)
            })
        
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def save_chunks(self, chunks: List[Document], output_path: str = None):
        """Save processed chunks to JSON"""
        if output_path is None:
            output_path = settings.PROCESSED_CHUNKS_PATH
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert to serializable format
        chunk_data = []
        for chunk in chunks:
            chunk_data.append({
                'text': chunk.page_content,
                'metadata': chunk.metadata
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(chunks)} chunks to {output_path}")
    
    def load_chunks(self, input_path: str = None) -> List[Document]:
        """Load processed chunks from JSON"""
        if input_path is None:
            input_path = settings.PROCESSED_CHUNKS_PATH

        if not os.path.exists(input_path):
            return []

        with open(input_path, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)

        chunks = []
        for idx, data in enumerate(chunk_data):
            try:
                chunk = Document(
                    page_content=data.get('text', ''),  # Default to empty string if missing
                    metadata=data.get('metadata', {})   # Default to empty dict if missing
                )
                chunks.append(chunk)
            except Exception as e:
                logger.warning(f"Skipping chunk at index {idx} due to error: {e}")

        logger.info(f"Loaded {len(chunks)} chunks from {input_path}")
        return chunks


def load_and_process_documents():
    """Main function to load and process all documents"""
    loader = EnhancedDocumentLoader()
    
    # Try to load existing chunks
    chunks = loader.load_chunks()
    
    if not chunks:
        logger.info("No existing chunks found. Processing documents...")
        # Load and process documents
        documents = loader.load_all_documents()
        
        if documents:
            chunks = loader.split_documents(documents)
            loader.save_chunks(chunks)
        else:
            logger.warning("No documents found to process")
            return []
    
    return chunks