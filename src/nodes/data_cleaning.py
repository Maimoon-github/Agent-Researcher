"""
Node 5: Data Cleaning & Preprocessing

Cleans text and prepares it for LLM processing.
"""

import re
from typing import Any, Dict, List
from datetime import datetime
import uuid

from loguru import logger

from .base import BaseNode
from ..core.state import AgentState


class DataCleaningNode(BaseNode):
    """
    Cleans and preprocesses validated data.
    
    Features:
    - Text cleaning and normalization
    - Chunking for LLM processing
    - Language detection
    - Entity extraction preparation
    """
    
    node_name = "data_cleaning"
    max_retries = 2
    
    # Chunk settings
    CHUNK_SIZE = 1500  # Characters per chunk
    CHUNK_OVERLAP = 200  # Overlap between chunks
    
    def validate_input(self, state: AgentState) -> tuple[bool, str]:
        """Check for validated data."""
        validated_data = state.get("validated_data", [])
        if not validated_data:
            return False, "No validated data to clean"
        return True, ""
    
    def process(self, state: AgentState) -> AgentState:
        """Clean and chunk all validated data."""
        validated_data = state.get("validated_data", [])
        
        logger.info(f"Cleaning {len(validated_data)} data items")
        
        cleaned_chunks = []
        
        for item in validated_data:
            try:
                # Clean the content
                cleaned_content = self._clean_text(item.get("content", ""))
                
                # Create chunks
                chunks = self._create_chunks(
                    cleaned_content,
                    source_id=item.get("source_id"),
                    metadata=item.get("metadata", {}),
                )
                
                cleaned_chunks.extend(chunks)
                
            except Exception as e:
                logger.warning(f"Cleaning error: {e}")
                self.add_warning(state, f"Cleaning failed for source {item.get('source_id')}: {e}")
        
        state["cleaned_chunks"] = cleaned_chunks
        logger.info(f"Created {len(cleaned_chunks)} chunks from {len(validated_data)} items")
        
        return state
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '[URL]', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+\.\S+', '[EMAIL]', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:\'\"\-\(\)\[\]\n]', '', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Remove very short lines (likely noise)
        lines = text.split('\n')
        lines = [line for line in lines if len(line.strip()) > 10 or line.strip() == '']
        text = '\n'.join(lines)
        
        return text.strip()
    
    def _create_chunks(
        self,
        text: str,
        source_id: str,
        metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks."""
        chunks = []
        
        if not text:
            return chunks
        
        # Try to split on paragraph boundaries first
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        current_start = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) < self.CHUNK_SIZE:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append(self._create_chunk_dict(
                        content=current_chunk,
                        source_id=source_id,
                        chunk_index=len(chunks),
                        metadata=metadata,
                    ))
                
                # Start new chunk with overlap
                if len(current_chunk) > self.CHUNK_OVERLAP:
                    overlap = current_chunk[-self.CHUNK_OVERLAP:]
                    current_chunk = overlap + "\n\n" + para
                else:
                    current_chunk = para
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(self._create_chunk_dict(
                content=current_chunk,
                source_id=source_id,
                chunk_index=len(chunks),
                metadata=metadata,
            ))
        
        # If no paragraphs, do simple character-based chunking
        if not chunks and text:
            for i in range(0, len(text), self.CHUNK_SIZE - self.CHUNK_OVERLAP):
                chunk_text = text[i:i + self.CHUNK_SIZE]
                chunks.append(self._create_chunk_dict(
                    content=chunk_text,
                    source_id=source_id,
                    chunk_index=len(chunks),
                    metadata=metadata,
                ))
        
        return chunks
    
    def _create_chunk_dict(
        self,
        content: str,
        source_id: str,
        chunk_index: int,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a chunk dictionary."""
        # Estimate token count (rough approximation)
        estimated_tokens = len(content) // 4
        
        return {
            "chunk_id": str(uuid.uuid4()),
            "source_id": source_id,
            "content": content,
            "chunk_index": chunk_index,
            "tokens": estimated_tokens,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata,
        }
