import logging
from typing import List, Dict, Any, Optional
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.schema import BaseRetriever, Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from pydantic import Field

from app.config import settings
from app.vector_store import EnhancedVectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomRetriever(BaseRetriever):
    """Custom retriever that uses our enhanced vector store"""
    
    # Declare vector_store as a Pydantic field
    vector_store: EnhancedVectorStore = Field(...)
    k: int = Field(default=5)
    
    class Config:
        arbitrary_types_allowed = True  # Allow non-standard types like EnhancedVectorStore
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Retrieve relevant documents for the query"""
        return self.vector_store.hybrid_search(query, k=self.k)

class LegalRAGEngine:
    """Advanced RAG engine for Indian Legal System queries"""
    
    def __init__(self, vector_store: EnhancedVectorStore):
        self.vector_store = vector_store
        self.llm = self._initialize_llm()
        self.retriever = CustomRetriever(vector_store=vector_store, k=settings.TOP_K_RETRIEVAL)
        self.qa_chain = self._create_qa_chain()
        
    def _initialize_llm(self) -> ChatGoogleGenerativeAI:
        """Initialize the Gemini LLM"""
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            convert_system_message_to_human=True
        )
    
    def _create_legal_prompt(self) -> PromptTemplate:
        """Create specialized prompt for legal queries"""
        template = """You are an expert AI assistant specializing in Indian law and legal system. Your role is to provide accurate, comprehensive, and helpful legal information based on the provided context.

CONTEXT:
{context}

QUERY: {question}

INSTRUCTIONS:
1. Analyze the provided legal context carefully
2. Provide accurate information based on Indian law
3. If the context contains relevant information, use it as the primary source
4. Structure your response clearly with proper legal terminology
5. Include relevant sections, articles, or case references when available
6. If the context is insufficient, clearly state the limitations
7. Always emphasize that this is informational and not a substitute for professional legal advice

RESPONSE GUIDELINES:
- Be comprehensive yet concise
- Use proper legal formatting and terminology
- Include citations to specific laws, sections, or cases when mentioned in context
- Organize information logically (overview, specific provisions, exceptions, etc.)
- End with a disclaimer about seeking professional legal counsel

LEGAL RESPONSE:"""

        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def _create_qa_chain(self):
        """Create the QA chain using LangChain"""
        prompt = self._create_legal_prompt()
        
        # Create RAG chain
        rag_chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain
    
    def query(self, question: str, **kwargs) -> Dict[str, Any]:
        """Process a legal query and return comprehensive response"""
        try:
            logger.info(f"Processing query: {question[:100]}...")
            
            # Get relevant context
            context_docs = self.retriever._get_relevant_documents(question, run_manager=None)
            
            # Generate response
            response = self.qa_chain.invoke(question)
            
            # Prepare source information
            sources = self._extract_sources(context_docs)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(question, context_docs, response)
            
            result = {
                "answer": response,
                "sources": sources,
                "confidence_score": confidence,
                "context_used": len(context_docs),
                "query_type": self._classify_query(question)
            }
            
            logger.info("Query processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "answer": "I apologize, but I encountered an error while processing your query. Please try rephrasing your question or contact support.",
                "sources": [],
                "confidence_score": 0.0,
                "context_used": 0,
                "query_type": "error",
                "error": str(e)
            }
    
    def _extract_sources(self, context_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract source information from context documents"""
        sources = []
        seen_sources = set()
        
        for doc in context_docs:
            source_info = {
                "source": doc.metadata.get("source", "Unknown"),
                "file_type": doc.metadata.get("file_type", "Unknown"),
                "chunk_id": doc.metadata.get("chunk_id", "Unknown"),
                "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            }
            
            # Avoid duplicate sources
            source_key = f"{source_info['source']}_{source_info['chunk_id']}"
            if source_key not in seen_sources:
                sources.append(source_info)
                seen_sources.add(source_key)
        
        return sources
    
    def _calculate_confidence(
        self, 
        question: str, 
        context_docs: List[Document], 
        response: str
    ) -> float:
        """Calculate confidence score for the response"""
        try:
            if not context_docs:
                return 0.1
            
            # Factors for confidence calculation
            factors = {
                "context_relevance": 0.0,
                "response_length": 0.0,
                "source_diversity": 0.0,
                "legal_keywords": 0.0
            }
            
            # Context relevance (based on number of relevant docs)
            factors["context_relevance"] = min(len(context_docs) / settings.TOP_K_RETRIEVAL, 1.0)
            
            # Response comprehensiveness
            response_length = len(response.split())
            factors["response_length"] = min(response_length / 200, 1.0)
            
            # Source diversity
            unique_sources = len(set(doc.metadata.get("source", "") for doc in context_docs))
            factors["source_diversity"] = min(unique_sources / 3, 1.0)
            
            # Legal keyword presence
            legal_keywords = [
                "section", "article", "act", "law", "provision", "clause", 
                "supreme court", "high court", "constitution", "ipc", "crpc", "cpc"
            ]
            response_lower = response.lower()
            keyword_count = sum(1 for keyword in legal_keywords if keyword in response_lower)
            factors["legal_keywords"] = min(keyword_count / 5, 1.0)
            
            # Weighted average
            weights = {
                "context_relevance": 0.3,
                "response_length": 0.2,
                "source_diversity": 0.3,
                "legal_keywords": 0.2
            }
            
            confidence = sum(factors[key] * weights[key] for key in factors)
            return round(confidence, 2)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _classify_query(self, question: str) -> str:
        """Classify the type of legal query"""
        question_lower = question.lower()
        
        classification_rules = {
            "criminal_law": ["ipc", "criminal", "murder", "theft", "assault", "bail", "arrest", "fir"],
            "civil_law": ["civil", "contract", "property", "tort", "damages", "suit", "plaintiff", "defendant"],
            "constitutional_law": ["constitution", "fundamental rights", "directive principles", "amendment"],
            "corporate_law": ["company", "corporate", "shares", "director", "merger", "acquisition"],
            "family_law": ["marriage", "divorce", "custody", "adoption", "inheritance", "succession"],
            "labor_law": ["employment", "labor", "worker", "wage", "termination", "union"],
            "tax_law": ["tax", "income tax", "gst", "customs", "excise"],
            "procedure": ["procedure", "process", "filing", "court", "appeal", "jurisdiction"],
            "general": []
        }
        
        for category, keywords in classification_rules.items():
            if any(keyword in question_lower for keyword in keywords):
                return category
        
        return "general"
    
    def get_similar_questions(self, question: str, k: int = 3) -> List[str]:
        """Get similar questions that might be relevant"""
        try:
            # This is a simplified version - in production, you might maintain
            # a database of common legal questions
            context_docs = self.retriever._get_relevant_documents(question, run_manager=None)
            
            # Extract potential questions from context
            similar_questions = []
            for doc in context_docs[:k]:
                content = doc.page_content
                # Simple heuristic to find question-like sentences
                sentences = content.split('.')
                for sentence in sentences:
                    if any(word in sentence.lower() for word in ['what', 'how', 'when', 'where', 'why', 'can', 'is', 'are']):
                        if len(sentence.strip()) > 10 and len(sentence.strip()) < 100:
                            similar_questions.append(sentence.strip() + "?")
            
            return similar_questions[:k]
            
        except Exception as e:
            logger.error(f"Error getting similar questions: {e}")
            return []
    
    def explain_legal_term(self, term: str) -> Dict[str, Any]:
        """Explain a specific legal term"""
        try:
            query = f"What is {term}? Define {term}. Explain {term} in Indian law."
            result = self.query(query)
            result["query_type"] = "definition"
            return result
            
        except Exception as e:
            logger.error(f"Error explaining term: {e}")
            return {
                "answer": f"I couldn't find a definition for '{term}'. Please try a more specific query.",
                "sources": [],
                "confidence_score": 0.0,
                "query_type": "definition_error"
            }