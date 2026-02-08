"""
Node 7: Semantic Indexing

Stores and indexes knowledge in vector database for retrieval.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from loguru import logger

from .base import BaseNode
from ..core.state import AgentState
from ..core.config import get_config
from ..core.llm_manager import get_llm_manager


class SemanticIndexingNode(BaseNode):
    """
    Indexes extracted knowledge in vector database.
    
    Features:
    - ChromaDB integration via VectorStore
    - Embedding generation
    - Semantic search
    - Metadata filtering
    """
    
    node_name = "semantic_indexing"
    max_retries = 2
    
    def __init__(self, config=None):
        super().__init__(config)
        self._vector_store = None
    
    @property
    def vector_store(self):
        """Lazy load VectorStore."""
        if self._vector_store is None:
            # Import here to avoid circular dependencies if any
            from ..storage.vector_store import VectorStore
            self._vector_store = VectorStore(
                collection_name=self.config.storage.vector_db.collection_name
            )
        return self._vector_store
    
    def validate_input(self, state: AgentState) -> tuple[bool, str]:
        """Check for extracted knowledge."""
        knowledge = state.get("extracted_knowledge", [])
        if not knowledge:
            # Not an error - might just be updating index
            logger.info("No new knowledge to index")
        return True, ""
    
    def process(self, state: AgentState) -> AgentState:
        """Index extracted knowledge."""
        knowledge_items = state.get("extracted_knowledge", [])
        
        if not knowledge_items:
            state["indexed_count"] = 0
            return state
        
        logger.info(f"Indexing {len(knowledge_items)} knowledge items")
        
        llm = get_llm_manager()
        indexed_count = 0
        
        # Prepare batch for indexing
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        for item in knowledge_items:
            try:
                # Create document text from knowledge
                doc_text = self._create_document_text(item)
                
                # Generate embedding
                embedding = llm.get_embeddings(doc_text)
                if embedding is None:
                    self.add_warning(state, f"Failed to generate embedding for {item.get('id')}")
                    continue
                
                # Prepare metadata
                metadata = self._prepare_metadata(item)
                
                ids.append(item.get("id", str(uuid.uuid4())))
                documents.append(doc_text)
                metadatas.append(metadata)
                embeddings.append(embedding)
                
                indexed_count += 1
                
            except Exception as e:
                logger.warning(f"Error preparing item for index: {e}")
                self.add_warning(state, f"Failed to prepare item: {e}")
        
        # Batch upsert via VectorStore
        if ids:
            try:
                self.vector_store.upsert(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )
                logger.info(f"Indexed {indexed_count} items to VectorStore")
            except Exception as e:
                logger.error(f"VectorStore upsert failed: {e}")
                self.add_warning(state, f"Database upsert failed: {e}")
        
        state["indexed_count"] = indexed_count
        
        return state
    
    def _create_document_text(self, item: Dict[str, Any]) -> str:
        """Create searchable document text from knowledge item."""
        parts = []
        
        if item.get("summary"):
            parts.append(item["summary"])
        
        if item.get("key_facts"):
            parts.append("Key facts: " + "; ".join(item["key_facts"]))
        
        if item.get("entities"):
            parts.append("Entities: " + ", ".join(item["entities"]))
        
        if item.get("content"):
            # Include first 500 chars of original content
            parts.append(item["content"][:500])
        
        return "\n".join(parts)
    
    def _prepare_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare metadata for ChromaDB (only primitive types)."""
        return {
            "source_id": str(item.get("source_id", "")),
            "chunk_id": str(item.get("chunk_id", "")),
            "relevance_score": float(item.get("relevance_score", 0.5)),
            "model_used": str(item.get("model_used", "")),
            "indexed_at": datetime.now().isoformat(),
            "tags": ",".join(item.get("tags", [])),  # Convert list to string
        }
    
    def search(
        self,
        query: str,
        n_results: int = 10,
        min_relevance: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base.
        """
        llm = get_llm_manager()
        query_embedding = llm.get_embeddings(query)
        
        if query_embedding is None:
            logger.error("Failed to generate query embedding")
            return []
        
        try:
            where = {"relevance_score": {"$gte": min_relevance}} if min_relevance > 0 else None
            
            results = self.vector_store.query(
                query_embedding=query_embedding,
                n_results=n_results,
                where=where,
            )
            
            # Format results
            formatted = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    formatted.append({
                        "id": results["ids"][0][i] if results.get("ids") else None,
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0,
                    })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            count = self.vector_store.count()
            return {
                "total_documents": count,
                "collection_name": self.config.storage.vector_db.collection_name,
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}
