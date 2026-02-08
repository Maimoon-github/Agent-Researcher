"""
Node 14: Knowledge Base Updater

Updates and maintains the knowledge base.
"""

from typing import Any, Dict, List
from datetime import datetime

from loguru import logger

from .base import BaseNode
from .semantic_indexing import SemanticIndexingNode
from ..core.state import AgentState
from ..core.llm_manager import get_llm_manager


class KBUpdaterNode(BaseNode):
    """
    Updates knowledge base based on feedback.
    
    Features:
    - Incremental indexing
    - Stale data cleanup
    - Quality-based re-ranking
    """
    
    node_name = "kb_updater"
    max_retries = 1
    
    def __init__(self, config=None):
        super().__init__(config)
        self._indexer = None
    
    @property
    def indexer(self) -> SemanticIndexingNode:
        """Get semantic indexing node."""
        if self._indexer is None:
            self._indexer = SemanticIndexingNode(self.config)
        return self._indexer
    
    def process(self, state: AgentState) -> AgentState:
        """Update knowledge base based on session results."""
        improvements = state.get("improvements", [])
        quality_review = state.get("quality_review", {})
        
        logger.info("Updating knowledge base")
        
        updates_made = []
        
        # If document was approved with high quality, boost related knowledge
        if quality_review.get("approved") and quality_review.get("score", 0) > 0.8:
            boost_result = self._boost_used_knowledge(state)
            if boost_result:
                updates_made.append(boost_result)
        
        # If there were quality issues, might need to flag problematic sources
        if quality_review.get("issues"):
            flag_result = self._flag_problematic_sources(state)
            if flag_result:
                updates_made.append(flag_result)
        
        # Log updates
        logger.info(f"KB updates: {len(updates_made)}")
        
        # Store update info in state
        if "metrics" in state:
            state["metrics"]["kb_updates"] = updates_made
        
        return state
    
    def _boost_used_knowledge(self, state: AgentState) -> Dict[str, Any]:
        """Boost relevance of knowledge used in successful documents."""
        query = state.get("query", "")
        if not query:
            return None
            
        try:
            vector_store = self.indexer.vector_store
            llm = get_llm_manager()
            embedding = llm.get_embeddings(query)
            
            if not embedding:
                return None
                
            # Find relevant items (these were likely used)
            # We assume top 10 relevant items contributed to the result
            results = vector_store.query(
                query_embedding=embedding,
                n_results=10
            )
            
            if not results or not results.get("ids"):
                return None
                
            ids = results["ids"][0]
            metadatas = results["metadatas"][0]
            
            updated_ids = []
            updated_metadatas = []
            
            for i, meta in enumerate(metadatas):
                doc_id = ids[i]
                # Boost relevance score
                current_score = float(meta.get("relevance_score", 0.5))
                # Increase by 10% but cap at 1.0
                new_score = min(1.0, current_score + 0.1)
                
                meta["relevance_score"] = new_score
                updated_ids.append(doc_id)
                updated_metadatas.append(meta)
                
            if updated_ids:
                vector_store.update(
                    ids=updated_ids,
                    metadatas=updated_metadatas
                )
                logger.info(f"Boosted relevance for {len(updated_ids)} items")
                return {
                    "action": "boost",
                    "items": len(updated_ids),
                    "reason": "Used in approved document (inferred relevance)",
                }
                
        except Exception as e:
            logger.warning(f"Failed to boost knowledge: {e}")
            
        return None
    
    def _flag_problematic_sources(self, state: AgentState) -> Dict[str, Any]:
        """Flag sources that led to quality issues."""
        issues = state.get("quality_review", {}).get("issues", [])
        
        # Analyze which sources might be problematic
        # We flag generalized issues for now as source attribution is complex
        
        if len(issues) > 5:
            return {
                "action": "flag",
                "reason": "High issue count in document",
                "issues": len(issues),
            }
        
        return None
