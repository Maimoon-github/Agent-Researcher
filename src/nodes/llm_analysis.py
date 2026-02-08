"""
Node 6: LLM Analysis & Extraction

Uses local LLMs to extract insights and structured knowledge.
"""

import json
import re
from typing import Any, Dict, List
from datetime import datetime
import uuid

from loguru import logger

from .base import BaseNode
from ..core.state import AgentState
from ..core.llm_manager import get_llm_manager


class LLMAnalysisNode(BaseNode):
    """
    Analyzes content using LLM for knowledge extraction.
    
    Features:
    - Entity extraction
    - Summarization
    - Key insight identification
    - Automatic model fallback on token limits
    """
    
    node_name = "llm_analysis"
    max_retries = 2
    
    def validate_input(self, state: AgentState) -> tuple[bool, str]:
        """Check for cleaned chunks."""
        chunks = state.get("cleaned_chunks", [])
        if not chunks:
            return False, "No cleaned chunks for analysis"
        return True, ""
    
    def process(self, state: AgentState) -> AgentState:
        """Analyze all chunks with LLM."""
        chunks = state.get("cleaned_chunks", [])
        query = state.get("query", "")
        
        logger.info(f"Analyzing {len(chunks)} chunks with LLM")
        
        llm = get_llm_manager()
        extracted_knowledge = []
        
        for chunk in chunks:
            try:
                knowledge = self._analyze_chunk(chunk, query, llm)
                if knowledge:
                    extracted_knowledge.append(knowledge)
                
            except Exception as e:
                logger.warning(f"Analysis error for chunk {chunk.get('chunk_id')}: {e}")
                self.add_warning(state, f"Analysis failed: {e}")
        
        state["extracted_knowledge"] = extracted_knowledge
        
        # Update model tracking in state
        state["current_model"] = llm.current_model
        state["model_switch_count"] = llm.model_switch_count
        
        # Update metrics
        if "metrics" in state:
            state["metrics"]["llm_calls"] = state["metrics"].get("llm_calls", 0) + len(chunks)
            state["metrics"]["total_tokens_used"] = llm.total_tokens_used
        
        logger.info(f"Extracted knowledge from {len(extracted_knowledge)} chunks")
        
        return state
    
    def _analyze_chunk(self, chunk: Dict[str, Any], query: str, llm) -> Dict[str, Any]:
        """Analyze a single chunk."""
        content = chunk.get("content", "")
        
        prompt = f"""Analyze the following text in the context of this research query:

Research Query: {query}

Text to Analyze:
{content}

Provide a JSON response with:
{{
    "summary": "A concise 2-3 sentence summary of the key points",
    "entities": ["list", "of", "key", "entities"],
    "key_facts": ["list of important facts or data points"],
    "relevance_score": 0.0 to 1.0 how relevant to the query,
    "tags": ["topic", "tags"]
}}

Be accurate and concise. Only include information present in the text."""

        response = llm.generate(
            prompt=prompt,
            system_prompt="You are a research analyst. Extract structured information from text. Always respond with valid JSON.",
            temperature=0.3,
            max_tokens=1000,
        )
        
        if not response.success:
            logger.warning(f"LLM analysis failed: {response.error}")
            return None
        
        # Parse response
        analysis = self._parse_analysis(response.content)
        if not analysis:
            return None
        
        return {
            "id": str(uuid.uuid4()),
            "chunk_id": chunk.get("chunk_id"),
            "source_id": chunk.get("source_id"),
            "content": content,
            "summary": analysis.get("summary", ""),
            "entities": analysis.get("entities", []),
            "key_facts": analysis.get("key_facts", []),
            "relevance_score": analysis.get("relevance_score", 0.5),
            "tags": analysis.get("tags", []),
            "model_used": response.model,
            "tokens_used": response.token_usage.total_tokens,
            "analyzed_at": datetime.now().isoformat(),
        }
    
    def _parse_analysis(self, content: str) -> Dict[str, Any]:
        """Parse LLM analysis response."""
        try:
            # Try to find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse analysis JSON: {e}")
        
        # Fallback: extract what we can
        return {
            "summary": content[:500] if content else "",
            "entities": [],
            "key_facts": [],
            "relevance_score": 0.5,
            "tags": [],
        }
