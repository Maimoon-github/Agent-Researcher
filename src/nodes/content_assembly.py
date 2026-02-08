"""
Node 8: Content Assembly Agent

Composes coherent documents from knowledge base using RAG.
"""

from typing import Any, Dict, List
from datetime import datetime
import uuid

from loguru import logger

from .base import BaseNode
from .semantic_indexing import SemanticIndexingNode
from ..core.state import AgentState
from ..core.llm_manager import get_llm_manager


class ContentAssemblyNode(BaseNode):
    """
    Assembles document content from knowledge base.
    
    Features:
    - RAG-based content retrieval
    - Document structure planning
    - Citation tracking
    - Context window management
    """
    
    node_name = "content_assembly"
    max_retries = 2
    
    def __init__(self, config=None):
        super().__init__(config)
        self._indexer = None
    
    @property
    def indexer(self) -> SemanticIndexingNode:
        """Get semantic indexing node for searches."""
        if self._indexer is None:
            self._indexer = SemanticIndexingNode(self.config)
        return self._indexer
    
    def validate_input(self, state: AgentState) -> tuple[bool, str]:
        """Check for query and indexed knowledge."""
        if not state.get("query"):
            return False, "No query for document assembly"
        return True, ""
    
    def process(self, state: AgentState) -> AgentState:
        """Assemble document from knowledge base."""
        query = state["query"]
        
        logger.info(f"Assembling document for: {query[:100]}...")
        
        llm = get_llm_manager()
        
        # Step 1: Plan document structure
        structure = self._plan_structure(query, llm)
        
        # Step 2: Retrieve relevant knowledge for each section
        sections = []
        citations = []
        
        for section in structure.get("sections", []):
            section_content, section_citations = self._assemble_section(
                section, query, llm
            )
            sections.append(section_content)
            citations.extend(section_citations)
        
        # Step 3: Create document draft
        document_draft = {
            "id": str(uuid.uuid4()),
            "title": structure.get("title", f"Research: {query[:50]}"),
            "query": query,
            "sections": sections,
            "citations": list(set(citations)),
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "model_used": llm.current_model,
                "knowledge_items_used": len(citations),
            },
        }
        
        state["document_draft"] = document_draft
        
        # Update model tracking
        state["current_model"] = llm.current_model
        state["model_switch_count"] = llm.model_switch_count
        
        logger.info(f"Assembled document with {len(sections)} sections")
        
        return state
    
    def _plan_structure(self, query: str, llm) -> Dict[str, Any]:
        """Plan document structure using LLM."""
        prompt = f"""Create a document structure for this research query:

Query: {query}

Provide a JSON response with:
{{
    "title": "Document title",
    "sections": [
        {{"heading": "Section 1", "focus": "What to cover"}},
        {{"heading": "Section 2", "focus": "What to cover"}}
    ]
}}

Create 3-5 logical sections. Be concise."""

        response = llm.generate(
            prompt=prompt,
            system_prompt="You are a technical writer. Plan document structures.",
            temperature=0.5,
            max_tokens=500,
        )
        
        if response.success:
            import json
            import re
            try:
                match = re.search(r'\{[\s\S]*\}', response.content)
                if match:
                    return json.loads(match.group())
            except:
                pass
        
        # Default structure
        return {
            "title": f"Research Report: {query[:50]}",
            "sections": [
                {"heading": "Introduction", "focus": "Overview and context"},
                {"heading": "Key Findings", "focus": "Main research findings"},
                {"heading": "Analysis", "focus": "Detailed analysis"},
                {"heading": "Conclusion", "focus": "Summary and recommendations"},
            ],
        }
    
    def _assemble_section(
        self,
        section: Dict[str, Any],
        query: str,
        llm,
    ) -> tuple[Dict[str, Any], List[str]]:
        """Assemble content for a single section."""
        heading = section.get("heading", "Section")
        focus = section.get("focus", "")
        
        # Search knowledge base
        search_query = f"{query} {focus}"
        knowledge = self.indexer.search(search_query, n_results=5)
        
        # Build context from knowledge
        context_parts = []
        citations = []
        
        for item in knowledge:
            context_parts.append(item.get("content", ""))
            if item.get("id"):
                citations.append(item["id"])
        
        context = "\n---\n".join(context_parts) if context_parts else "No relevant knowledge found."
        
        # Generate section content
        prompt = f"""Write the "{heading}" section for a research document.

Research Query: {query}
Section Focus: {focus}

Available Knowledge:
{context[:3000]}

Write a well-structured section with:
- Clear, professional prose
- Specific facts and data from the knowledge
- Logical flow

Write 2-4 paragraphs. Be informative and accurate."""

        response = llm.generate(
            prompt=prompt,
            system_prompt="You are an expert technical writer. Write clear, accurate content based on provided knowledge.",
            temperature=0.7,
            max_tokens=1500,
        )
        
        content = response.content if response.success else f"[Content generation failed for {heading}]"
        
        return {
            "heading": heading,
            "content": content,
            "knowledge_items": len(knowledge),
        }, citations
