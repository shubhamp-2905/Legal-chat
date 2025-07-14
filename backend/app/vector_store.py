import os
import pickle
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedVectorStore:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.vectorstore: Optional[FAISS] = None
        self.documents: List[Document] = []
        self.metadata_index: Dict[str, Any] = {}
        
    def build_index(self, documents: List[Document]) -> bool:
        """Build FAISS index from documents"""
        try:
            if not documents:
                logger.error("No documents provided for indexing")
                return False
            
            self.documents = documents
            logger.info(f"Building vector index for {len(documents)} documents...")
            
            # Create vector store
            self.vectorstore = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
            
            # Build metadata index for fast lookup
            self._build_metadata_index()
            
            # Save index
            self._save_index()
            
            logger.info("Vector index built successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error building vector index: {e}")
            return False
    
    def _build_metadata_index(self):
        """Build metadata index for efficient filtering"""
        self.metadata_index = {
            'sources': set(),
            'file_types': set(),
            'doc_ids': set()
        }
        
        for doc in self.documents:
            metadata = doc.metadata
            if 'source' in metadata:
                self.metadata_index['sources'].add(metadata['source'])
            if 'file_type' in metadata:
                self.metadata_index['file_types'].add(metadata['file_type'])
            if 'doc_id' in metadata:
                self.metadata_index['doc_ids'].add(metadata['doc_id'])
    
    def load_index(self) -> bool:
        """Load existing FAISS index"""
        try:
            index_path = settings.VECTOR_INDEX_PATH
            if os.path.exists(f"{index_path}.faiss"):
                self.vectorstore = FAISS.load_local(
                    index_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                
                # Load metadata
                metadata_path = f"{index_path}_metadata.pkl"
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'rb') as f:
                        self.metadata_index = pickle.load(f)
                
                logger.info("Vector index loaded successfully")
                return True
            else:
                logger.info("No existing vector index found")
                return False
                
        except Exception as e:
            logger.error(f"Error loading vector index: {e}")
            return False
    
    def _save_index(self):
        """Save FAISS index and metadata"""
        try:
            index_path = settings.VECTOR_INDEX_PATH
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            
            # Save FAISS index
            self.vectorstore.save_local(index_path)
            
            # Save metadata
            metadata_path = f"{index_path}_metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.metadata_index, f)
            
            logger.info(f"Vector index saved to {index_path}")
            
        except Exception as e:
            logger.error(f"Error saving vector index: {e}")
    
    def similarity_search(
        self, 
        query: str, 
        k: int = None,
        filter_dict: Dict[str, Any] = None,
        score_threshold: float = 0.0
    ) -> List[Tuple[Document, float]]:
        """Enhanced similarity search with filtering and scoring"""
        if not self.vectorstore:
            logger.error("Vector store not initialized")
            return []
        
        if k is None:
            k = settings.TOP_K_RETRIEVAL
        
        try:
            # Perform similarity search with scores
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k * 2,  # Get more results for filtering
                filter=filter_dict
            )
            
            # Apply score threshold
            filtered_results = [
                (doc, score) for doc, score in results 
                if score >= score_threshold
            ]
            
            # Sort by score (lower is better for FAISS)
            filtered_results.sort(key=lambda x: x[1])
            
            # Return top k results
            return filtered_results[:k]
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    def hybrid_search(
        self, 
        query: str, 
        k: int = None,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7
    ) -> List[Document]:
        """Hybrid search combining keyword and semantic search"""
        if k is None:
            k = settings.TOP_K_RETRIEVAL
        
        # Semantic search
        semantic_results = self.similarity_search(query, k=k)
        
        # Simple keyword search
        keyword_results = self._keyword_search(query, k=k)
        
        # Combine results with weighted scoring
        combined_scores = {}
        
        # Add semantic scores
        for doc, score in semantic_results:
            doc_id = doc.metadata.get('doc_id', id(doc))
            combined_scores[doc_id] = {
                'doc': doc,
                'semantic_score': 1.0 / (1.0 + score),  # Convert to similarity
                'keyword_score': 0.0
            }
        
        # Add keyword scores
        for doc, score in keyword_results:
            doc_id = doc.metadata.get('doc_id', id(doc))
            if doc_id in combined_scores:
                combined_scores[doc_id]['keyword_score'] = score
            else:
                combined_scores[doc_id] = {
                    'doc': doc,
                    'semantic_score': 0.0,
                    'keyword_score': score
                }
        
        # Calculate final scores
        final_results = []
        for doc_id, scores in combined_scores.items():
            final_score = (
                semantic_weight * scores['semantic_score'] +
                keyword_weight * scores['keyword_score']
            )
            final_results.append((scores['doc'], final_score))
        
        # Sort by final score (higher is better)
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in final_results[:k]]
    
    def _keyword_search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Simple keyword-based search"""
        if not self.documents:
            return []
        
        query_terms = set(query.lower().split())
        scored_docs = []
        
        for doc in self.documents:
            content = doc.page_content.lower()
            content_terms = set(content.split())
            
            # Calculate Jaccard similarity
            intersection = query_terms.intersection(content_terms)
            union = query_terms.union(content_terms)
            
            if union:
                score = len(intersection) / len(union)
                if score > 0:
                    scored_docs.append((doc, score))
        
        # Sort by score (higher is better)
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_docs[:k]
    
    def get_relevant_context(
        self, 
        query: str, 
        max_context_length: int = 2000
    ) -> List[str]:
        """Get relevant context with length optimization"""
        results = self.hybrid_search(query)
        
        context_chunks = []
        total_length = 0
        
        for doc in results:
            content = doc.page_content
            
            # Add chunk if it fits within the limit
            if total_length + len(content) <= max_context_length:
                context_chunks.append(content)
                total_length += len(content)
            else:
                # Truncate the last chunk to fit
                remaining_space = max_context_length - total_length
                if remaining_space > 100:  # Only add if meaningful content can fit
                    truncated_content = content[:remaining_space] + "..."
                    context_chunks.append(truncated_content)
                break
        
        return context_chunks
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        if not self.vectorstore:
            return {}
        
        return {
            'total_documents': len(self.documents),
            'unique_sources': len(self.metadata_index.get('sources', set())),
            'file_types': list(self.metadata_index.get('file_types', set())),
            'embedding_dimension': settings.VECTOR_DIMENSION,
            'embedding_model': settings.EMBEDDING_MODEL
        }
    
    def add_documents(self, new_documents: List[Document]) -> bool:
        """Add new documents to existing index"""
        try:
            if not self.vectorstore:
                return self.build_index(new_documents)
            
            # Add to existing vectorstore
            self.vectorstore.add_documents(new_documents)
            
            # Update documents list
            self.documents.extend(new_documents)
            
            # Update metadata index
            for doc in new_documents:
                metadata = doc.metadata
                if 'source' in metadata:
                    self.metadata_index['sources'].add(metadata['source'])
                if 'file_type' in metadata:
                    self.metadata_index['file_types'].add(metadata['file_type'])
                if 'doc_id' in metadata:
                    self.metadata_index['doc_ids'].add(metadata['doc_id'])
            
            # Save updated index
            self._save_index()
            
            logger.info(f"Added {len(new_documents)} new documents to index")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False