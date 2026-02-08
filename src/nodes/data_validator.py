"""
Node 4: Data Validator

Validates and normalizes data from multiple sources.
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib

from loguru import logger

from .base import BaseNode
from ..core.state import AgentState


class DataValidatorNode(BaseNode):
    """
    Validates and normalizes incoming data.
    
    Features:
    - Schema validation
    - Content quality checks
    - Deduplication
    - Normalization
    """
    
    node_name = "data_validator"
    max_retries = 2
    
    # Minimum content length to be considered valid
    MIN_CONTENT_LENGTH = 100
    # Maximum content length (to avoid processing huge files)
    MAX_CONTENT_LENGTH = 500000
    
    def validate_input(self, state: AgentState) -> tuple[bool, str]:
        """Check for raw data to validate."""
        raw_data = state.get("raw_data", [])
        if not raw_data:
            return False, "No raw data to validate"
        return True, ""
    
    def process(self, state: AgentState) -> AgentState:
        """Validate and normalize all raw data."""
        raw_data = state.get("raw_data", [])
        
        logger.info(f"Validating {len(raw_data)} data items")
        
        validated_data = []
        content_hashes = set()
        
        for item in raw_data:
            try:
                # Validate structure
                if not self._validate_structure(item):
                    self.add_warning(state, f"Invalid structure for item {item.get('id', 'unknown')}")
                    continue
                
                # Normalize content
                normalized = self._normalize_content(item)
                
                # Check content quality
                if not self._check_content_quality(normalized):
                    self.add_warning(state, f"Low quality content from {item.get('source_id', 'unknown')}")
                    continue
                
                # Deduplicate
                content_hash = self._compute_hash(normalized["content"])
                if content_hash in content_hashes:
                    logger.debug(f"Duplicate content skipped: {item.get('id')}")
                    continue
                content_hashes.add(content_hash)
                
                # Add validation metadata
                normalized["validation"] = {
                    "validated_at": datetime.now().isoformat(),
                    "content_hash": content_hash,
                    "quality_score": self._calculate_quality_score(normalized),
                }
                
                validated_data.append(normalized)
                
            except Exception as e:
                logger.warning(f"Validation error for item: {e}")
                self.add_warning(state, f"Validation failed: {e}")
        
        state["validated_data"] = validated_data
        logger.info(f"Validated {len(validated_data)}/{len(raw_data)} items")
        
        return state
    
    def _validate_structure(self, item: Dict[str, Any]) -> bool:
        """Check required fields exist."""
        required_fields = ["content", "source_id"]
        return all(field in item and item[field] for field in required_fields)
    
    def _normalize_content(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize content format."""
        content = item.get("content", "")
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # Remove null bytes and control characters
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)
        
        # Normalize unicode
        content = content.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Truncate if too long
        if len(content) > self.MAX_CONTENT_LENGTH:
            content = content[:self.MAX_CONTENT_LENGTH]
            logger.warning(f"Content truncated to {self.MAX_CONTENT_LENGTH} chars")
        
        normalized = item.copy()
        normalized["content"] = content
        normalized["content_length"] = len(content)
        
        return normalized
    
    def _check_content_quality(self, item: Dict[str, Any]) -> bool:
        """Check if content meets quality standards."""
        content = item.get("content", "")
        
        # Minimum length
        if len(content) < self.MIN_CONTENT_LENGTH:
            return False
        
        # Check for meaningful content (not just whitespace or symbols)
        alpha_ratio = sum(c.isalpha() for c in content) / max(len(content), 1)
        if alpha_ratio < 0.3:
            return False
        
        # Check for repetitive content
        if self._is_repetitive(content):
            return False
        
        return True
    
    def _is_repetitive(self, content: str) -> bool:
        """Check if content is overly repetitive."""
        # Simple check: if a phrase repeats too many times
        words = content.lower().split()
        if len(words) < 20:
            return False
        
        # Check for repeated phrases
        phrase_length = 5
        phrases = [' '.join(words[i:i+phrase_length]) for i in range(len(words) - phrase_length)]
        
        from collections import Counter
        phrase_counts = Counter(phrases)
        most_common = phrase_counts.most_common(1)
        
        if most_common and most_common[0][1] > len(phrases) * 0.1:
            return True
        
        return False
    
    def _compute_hash(self, content: str) -> str:
        """Compute hash for deduplication."""
        # Use first 10000 chars for hash to handle large content
        sample = content[:10000].lower()
        return hashlib.md5(sample.encode()).hexdigest()
    
    def _calculate_quality_score(self, item: Dict[str, Any]) -> float:
        """Calculate quality score (0-1)."""
        content = item.get("content", "")
        score = 0.5  # Base score
        
        # Length bonus
        if len(content) > 1000:
            score += 0.1
        if len(content) > 5000:
            score += 0.1
        
        # Structure bonus (has paragraphs)
        if "\n" in content:
            score += 0.1
        
        # Vocabulary diversity
        words = content.lower().split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            score += unique_ratio * 0.2
        
        return min(score, 1.0)
