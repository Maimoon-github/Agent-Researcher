"""
Query Analyzer - Phase 1: Query Analysis & Intent Understanding
"""

from typing import List, Dict, Tuple, Optional
import re
from enum import Enum
import logging


class QueryType(Enum):
    """Types of research queries"""
    FACTUAL = "factual"
    EXPLORATORY = "exploratory"
    COMPARATIVE = "comparative"
    TEMPORAL = "temporal"
    UNKNOWN = "unknown"


class QueryIntent(Enum):
    """Intent classification for queries"""
    FACT_FINDING = "fact_finding"
    LITERATURE_REVIEW = "literature_review"
    CURRENT_EVENTS = "current_events"
    DATA_COLLECTION = "data_collection"
    UNKNOWN = "unknown"


class AuthorityLevel(Enum):
    """Required authority level for sources"""
    HIGH = "high"  # Academic, government
    MEDIUM = "medium"  # News, professional
    LOW = "low"  # Blogs, forums


class TemporalRequirement(Enum):
    """Temporal requirements for sources"""
    HISTORICAL = "historical"
    RECENT = "recent"
    REAL_TIME = "real_time"
    ANY = "any"


class QueryAnalyzer:
    """Analyzes and normalizes research queries"""
    
    # Common stop words to remove
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'what', 'when', 'where', 'who', 'why'
    }
    
    # Keywords indicating different query types
    ACADEMIC_KEYWORDS = {
        'research', 'study', 'analysis', 'paper', 'journal', 'academic',
        'peer-reviewed', 'publication', 'thesis', 'dissertation', 'review'
    }
    
    TECHNICAL_KEYWORDS = {
        'code', 'programming', 'software', 'api', 'documentation', 'library',
        'framework', 'algorithm', 'implementation', 'technical'
    }
    
    NEWS_KEYWORDS = {
        'news', 'latest', 'recent', 'current', 'today', 'breaking', 'update',
        'announcement', 'report', 'development'
    }
    
    COMPARATIVE_KEYWORDS = {
        'compare', 'versus', 'vs', 'difference', 'comparison', 'contrast',
        'between', 'better', 'worse', 'alternative'
    }
    
    TEMPORAL_KEYWORDS = {
        'history', 'historical', 'evolution', 'timeline', 'past', 'origin',
        'development', 'background', 'when', 'since'
    }
    
    AGENT_KEYWORDS = {
        'agent', 'system', 'researcher', 'bot', 'you', 'your', 'capabilities',
        'features', 'architecture', 'implementation', 'how do you work',
        'what can you do', 'node', 'workflow', 'discovery'
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze(self, query: str) -> Dict:
        """
        Analyze a research query and extract intent, entities, and requirements.
        
        Args:
            query: The research query string
            
        Returns:
            Dictionary containing analysis results
        """
        # Step 1.1: Query Normalization
        normalized_query = self._normalize_query(query)
        search_terms = self._extract_search_terms(normalized_query)
        key_phrases = self._extract_key_phrases(normalized_query)
        entities = self._extract_named_entities(normalized_query)
        
        # Step 1.2: Intent Classification
        query_type = self._classify_query_type(normalized_query)
        intent = self._classify_intent(normalized_query)
        authority_level = self._determine_authority_level(intent, normalized_query)
        temporal_req = self._determine_temporal_requirement(normalized_query)
        
        # Step 1.3: Domain-Specific Processing
        domain_hints = self._identify_domain_hints(normalized_query)
        
        return {
            'original_query': query,
            'normalized_query': normalized_query,
            'search_terms': search_terms,
            'key_phrases': key_phrases,
            'entities': entities,
            'query_type': query_type.value,
            'intent': intent.value,
            'authority_level': authority_level.value,
            'temporal_requirement': temporal_req.value,
            'domain_hints': domain_hints
        }
    
    def _normalize_query(self, query: str) -> str:
        """Normalize the query string"""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Remove harmful characters (basic sanitization)
        query = re.sub(r'[<>\"\'%;()&+]', '', query)
        
        # Convert to lowercase for processing
        return query.lower()
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract meaningful search terms by removing stop words"""
        words = query.split()
        
        # Remove stop words
        meaningful_words = [
            word for word in words 
            if word not in self.STOP_WORDS and len(word) > 2
        ]
        
        return meaningful_words
    
    def _extract_key_phrases(self, query: str) -> List[str]:
        """Extract key phrases using simple n-gram approach"""
        words = query.split()
        phrases = []
        
        # Extract bigrams and trigrams
        for i in range(len(words) - 1):
            # Bigrams
            bigram = f"{words[i]} {words[i+1]}"
            if not all(w in self.STOP_WORDS for w in [words[i], words[i+1]]):
                phrases.append(bigram)
            
            # Trigrams
            if i < len(words) - 2:
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                if not all(w in self.STOP_WORDS for w in [words[i], words[i+1], words[i+2]]):
                    phrases.append(trigram)
        
        return phrases[:10]  # Return top 10 phrases
    
    def _extract_named_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract named entities (simplified version without spaCy for this implementation)
        In production, use spaCy NER
        """
        entities = {
            'organizations': [],
            'locations': [],
            'people': [],
            'dates': []
        }
        
        # Simple capitalized word detection (very basic)
        words = query.split()
        for i, word in enumerate(words):
            # Look for capitalized words in original query
            if i < len(query.split()) and query.split()[i][0].isupper():
                if len(word) > 2:
                    entities['organizations'].append(word)
        
        # Date patterns
        date_patterns = [
            r'\b\d{4}\b',  # Year
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities['dates'].extend(matches)
        
        return entities
    
    def _classify_query_type(self, query: str) -> QueryType:
        """Classify the type of query"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in self.COMPARATIVE_KEYWORDS):
            return QueryType.COMPARATIVE
        elif any(kw in query_lower for kw in self.TEMPORAL_KEYWORDS):
            return QueryType.TEMPORAL
        elif '?' in query or any(kw in query_lower for kw in ['what', 'who', 'when', 'where']):
            return QueryType.FACTUAL
        else:
            return QueryType.EXPLORATORY
    
    def _classify_intent(self, query: str) -> QueryIntent:
        """Classify the intent of the query"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in self.ACADEMIC_KEYWORDS):
            return QueryIntent.LITERATURE_REVIEW
        elif any(kw in query_lower for kw in self.NEWS_KEYWORDS):
            return QueryIntent.CURRENT_EVENTS
        elif any(kw in query_lower for kw in ['data', 'dataset', 'statistics', 'numbers']):
            return QueryIntent.DATA_COLLECTION
        elif '?' in query or 'what is' in query_lower or 'who is' in query_lower:
            return QueryIntent.FACT_FINDING
        else:
            return QueryIntent.UNKNOWN
    
    def _determine_authority_level(self, intent: QueryIntent, query: str) -> AuthorityLevel:
        """Determine required authority level based on intent"""
        if intent in [QueryIntent.LITERATURE_REVIEW, QueryIntent.DATA_COLLECTION]:
            return AuthorityLevel.HIGH
        elif intent == QueryIntent.CURRENT_EVENTS:
            return AuthorityLevel.MEDIUM
        elif any(kw in query.lower() for kw in self.ACADEMIC_KEYWORDS):
            return AuthorityLevel.HIGH
        else:
            return AuthorityLevel.MEDIUM
    
    def _determine_temporal_requirement(self, query: str) -> TemporalRequirement:
        """Determine temporal requirements for sources"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ['latest', 'recent', 'current', 'today', 'now']):
            return TemporalRequirement.RECENT
        elif any(kw in query_lower for kw in ['real-time', 'live', 'breaking']):
            return TemporalRequirement.REAL_TIME
        elif any(kw in query_lower for kw in self.TEMPORAL_KEYWORDS):
            return TemporalRequirement.HISTORICAL
        else:
            return TemporalRequirement.ANY
    
    def _identify_domain_hints(self, query: str) -> Dict[str, bool]:
        """Identify domain-specific hints in the query"""
        query_lower = query.lower()
        
        is_agent_query = any(kw in query_lower for kw in self.AGENT_KEYWORDS)
        
        return {
            'academic': any(kw in query_lower for kw in self.ACADEMIC_KEYWORDS),
            'technical': any(kw in query_lower for kw in self.TECHNICAL_KEYWORDS) or is_agent_query,
            'news': any(kw in query_lower for kw in self.NEWS_KEYWORDS),
            'local': any(kw in query_lower for kw in ['local', 'file', 'document', 'folder']) or is_agent_query,
            'agent': is_agent_query
        }