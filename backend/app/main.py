import logging
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import time

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from app.config import settings
from app.data_loader import load_and_process_documents
from app.vector_store import EnhancedVectorStore
from app.rag_engine import LegalRAGEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for storing the RAG system components
vector_store: Optional[EnhancedVectorStore] = None
rag_engine: Optional[LegalRAGEngine] = None

async def initialize_rag_system():
    """Initialize the RAG system components"""
    global vector_store, rag_engine
    
    try:
        logger.info("Initializing RAG system...")
        
        # Initialize vector store
        vector_store = EnhancedVectorStore()
        
        # Try to load existing index
        if not vector_store.load_index():
            logger.info("Building new vector index...")
            # Load and process documents
            documents = load_and_process_documents()
            
            if not documents:
                logger.error("No documents found. Please add legal documents to the data/legal_docs folder.")
                raise Exception("No documents available for indexing")
            
            # Build vector index
            success = vector_store.build_index(documents)
            if not success:
                raise Exception("Failed to build vector index")
        
        # Initialize RAG engine
        rag_engine = LegalRAGEngine(vector_store)
        
        logger.info("RAG system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    logger.info("Starting Legal RAG Chatbot...")
    await initialize_rag_system()
    yield
    # Shutdown
    logger.info("Shutting down Legal RAG Chatbot...")

# Create FastAPI app
app = FastAPI(
    title="Indian Legal System RAG Chatbot",
    description="Advanced RAG-based chatbot for Indian legal queries using LangChain and Gemini",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Pydantic models for API requests/responses
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="Legal question to ask")
    include_sources: bool = Field(default=True, description="Include source information in response")
    max_sources: int = Field(default=5, ge=1, le=10, description="Maximum number of sources to return")

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    confidence_score: float
    context_used: int
    query_type: str
    response_time: float
    similar_questions: List[str] = []

class TermExplanationRequest(BaseModel):
    term: str = Field(..., min_length=1, max_length=100, description="Legal term to explain")

class SystemStatsResponse(BaseModel):
    total_documents: int
    unique_sources: int
    file_types: List[str]
    embedding_model: str
    system_status: str

class HealthResponse(BaseModel):
    status: str
    timestamp: float
    system_ready: bool

# Dependency to get RAG engine
async def get_rag_engine() -> LegalRAGEngine:
    """Dependency to get the RAG engine"""
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    return rag_engine

async def get_vector_store() -> EnhancedVectorStore:
    """Dependency to get the vector store"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    return vector_store

# API Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Indian Legal System RAG Chatbot API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    system_ready = rag_engine is not None and vector_store is not None
    return HealthResponse(
        status="healthy" if system_ready else "initializing",
        timestamp=time.time(),
        system_ready=system_ready
    )

@app.post("/ask", response_model=ChatResponse)
async def ask_legal_question(
    request: QueryRequest,
    engine: LegalRAGEngine = Depends(get_rag_engine)
):
    """Main endpoint for asking legal questions"""
    try:
        start_time = time.time()
        
        # Process the query
        result = engine.query(request.question)
        
        # Get similar questions
        similar_questions = engine.get_similar_questions(request.question)
        
        # Prepare response
        response = ChatResponse(
            answer=result["answer"],
            sources=result["sources"][:request.max_sources] if request.include_sources else [],
            confidence_score=result["confidence_score"],
            context_used=result["context_used"],
            query_type=result["query_type"],
            response_time=round(time.time() - start_time, 2),
            similar_questions=similar_questions
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.post("/explain-term", response_model=ChatResponse)
async def explain_legal_term(
    request: TermExplanationRequest,
    engine: LegalRAGEngine = Depends(get_rag_engine)
):
    """Explain a specific legal term"""
    try:
        start_time = time.time()
        
        result = engine.explain_legal_term(request.term)
        
        response = ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence_score=result["confidence_score"],
            context_used=result.get("context_used", 0),
            query_type=result["query_type"],
            response_time=round(time.time() - start_time, 2)
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error explaining term: {e}")
        raise HTTPException(status_code=500, detail=f"Error explaining term: {str(e)}")

@app.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(store: EnhancedVectorStore = Depends(get_vector_store)):
    """Get system statistics"""
    try:
        stats = store.get_document_stats()
        
        return SystemStatsResponse(
            total_documents=stats.get("total_documents", 0),
            unique_sources=stats.get("unique_sources", 0),
            file_types=stats.get("file_types", []),
            embedding_model=stats.get("embedding_model", "unknown"),
            system_status="operational"
        )
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.get("/similar-questions/{question}")
async def get_similar_questions(
    question: str,
    k: int = 3,
    engine: LegalRAGEngine = Depends(get_rag_engine)
):
    """Get similar questions for a given query"""
    try:
        similar_questions = engine.get_similar_questions(question, k=k)
        return {"similar_questions": similar_questions}
        
    except Exception as e:
        logger.error(f"Error getting similar questions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting similar questions: {str(e)}")

@app.post("/reindex")
async def reindex_documents(
    background_tasks: BackgroundTasks,
    store: EnhancedVectorStore = Depends(get_vector_store)
):
    """Reindex all documents (background task)"""
    try:
        async def reindex_task():
            logger.info("Starting document reindexing...")
            documents = load_and_process_documents()
            if documents:
                store.build_index(documents)
                logger.info("Document reindexing completed")
            else:
                logger.warning("No documents found for reindexing")
        
        background_tasks.add_task(reindex_task)
        
        return {"message": "Document reindexing started in background"}
        
    except Exception as e:
        logger.error(f"Error starting reindex: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting reindex: {str(e)}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": time.time()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )