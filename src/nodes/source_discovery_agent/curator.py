"""
Curator - Phase 4: Source curation and ranking
"""

from typing import List, Dict, Optional
import logging
from collections import defaultdict
from urllib.parse import urlparse


class SourceCurator:
    """Curates and ranks sources for optimal research coverage"""
    
    def __init__(
        self,
        diversity_weight: float = 0.3,
        relevance_weight: float = 0.4,
        credibility_weight: float = 0.3,
        logger: Optional[logging.Logger] = None
    ):
        self.diversity_weight = diversity_weight
        self.relevance_weight = relevance_weight
        self.credibility_weight = credibility_weight
        self.logger = logger or logging.getLogger(__name__)
        
        # Validate weights sum to 1.0
        total_weight = diversity_weight + relevance_weight + credibility_weight
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def curate_sources(
        self,
        validated_sources: List[Dict],
        query_analysis: Dict,
        max_sources: int = 20
    ) -> Dict:
        """
        Curate and rank validated sources
        
        Args:
            validated_sources: List of validated source dictionaries
            query_analysis: Results from QueryAnalyzer
            max_sources: Maximum number of sources to return
            
        Returns:
            Dictionary with curated sources and recommendations
        """
        if not validated_sources:
            return {
                'ranked_sources': [],
                'source_types_identified': [],
                'primary_source_clusters': [],
                'coverage_gaps': [],
                'confidence_level': 0.0
            }
        
        # Phase 4.1: Diversity Optimization
        diversity_scores = self._calculate_diversity_scores(validated_sources)
        
        # Phase 4.2: Relevance Ranking
        relevance_scores = self._calculate_relevance_scores(
            validated_sources,
            query_analysis
        )
        
        # Phase 4.3: Combine scores and rank
        ranked_sources = self._rank_sources(
            validated_sources,
            diversity_scores,
            relevance_scores
        )
        
        # Select top sources
        top_sources = ranked_sources[:max_sources]
        
        # Identify source clusters
        clusters = self._identify_source_clusters(top_sources)
        
        # Identify coverage gaps
        gaps = self._identify_coverage_gaps(top_sources, query_analysis)
        
        # Calculate confidence level
        confidence = self._calculate_confidence_level(top_sources, query_analysis)
        
        # Extract unique source types
        source_types = list(set(source.get('source_type', 'web') for source in top_sources))
        
        return {
            'ranked_sources': top_sources,
            'source_types_identified': source_types,
            'primary_source_clusters': clusters,
            'coverage_gaps': gaps,
            'confidence_level': confidence,
            'diversity_score': self._calculate_overall_diversity(top_sources),
            'avg_credibility': sum(s.get('credibility_score', 0) for s in top_sources) / len(top_sources) if top_sources else 0
        }
    
    def _calculate_diversity_scores(self, sources: List[Dict]) -> Dict[int, float]:
        """Calculate diversity scores for sources"""
        diversity_scores = {}
        
        # Group sources by domain
        domain_counts = defaultdict(int)
        for source in sources:
            domain = source.get('domain', '')
            domain_counts[domain] += 1
        
        # Calculate diversity score for each source
        for idx, source in enumerate(sources):
            domain = source.get('domain', '')
            
            # Lower score for over-represented domains
            domain_frequency = domain_counts[domain]
            diversity_score = 1.0 / (1.0 + domain_frequency * 0.1)
            
            # Bonus for different source types
            source_type = source.get('source_type', 'web')
            if source_type in ['academic', 'government']:
                diversity_score *= 1.2
            
            diversity_scores[idx] = min(1.0, diversity_score)
        
        return diversity_scores
    
    def _calculate_relevance_scores(
        self,
        sources: List[Dict],
        query_analysis: Dict
    ) -> Dict[int, float]:
        """Calculate relevance scores for sources"""
        relevance_scores = {}
        search_terms = set(query_analysis.get('search_terms', []))
        
        if not search_terms:
            # If no search terms, all sources get equal relevance
            return {idx: 0.5 for idx in range(len(sources))}
        
        for idx, source in enumerate(sources):
            url = (source.get('url') or '').lower()
            title = (source.get('metadata', {}).get('title_extracted') or '').lower()
            snippet = (source.get('metadata', {}).get('snippet') or '').lower()
            
            # Count term matches in URL, title and snippet
            matches = 0
            for term in search_terms:
                if term in url or term in title or term in snippet:
                    matches += 1
            
            # Calculate relevance as percentage of terms matched
            relevance_score = matches / len(search_terms) if search_terms else 0.5
            
            # Boost for exact query match
            query = (query_analysis.get('normalized_query') or '').lower()
            if (query and url and query in url) or (query and title and query in title) or (query and snippet and query in snippet):
                relevance_score = min(1.0, relevance_score + 0.3)
            
            relevance_scores[idx] = relevance_score
        
        return relevance_scores
    
    def _rank_sources(
        self,
        sources: List[Dict],
        diversity_scores: Dict[int, float],
        relevance_scores: Dict[int, float]
    ) -> List[Dict]:
        """Rank sources using weighted combination of scores"""
        ranked_sources = []
        
        for idx, source in enumerate(sources):
            # Get component scores
            credibility = source.get('credibility_score', 0.0)
            diversity = diversity_scores.get(idx, 0.5)
            relevance = relevance_scores.get(idx, 0.5)
            
            # Calculate composite score
            composite_score = (
                self.credibility_weight * credibility +
                self.diversity_weight * diversity +
                self.relevance_weight * relevance
            )
            
            # Add composite score to source
            source_copy = source.copy()
            source_copy['composite_score'] = composite_score
            source_copy['ranking_details'] = {
                'credibility': credibility,
                'diversity': diversity,
                'relevance': relevance
            }
            
            ranked_sources.append(source_copy)
        
        # Sort by composite score (descending)
        ranked_sources.sort(key=lambda x: x['composite_score'], reverse=True)
        
        return ranked_sources
    
    def _identify_source_clusters(self, sources: List[Dict]) -> List[str]:
        """Identify primary source clusters (domains)"""
        domain_counts = defaultdict(int)
        
        for source in sources:
            domain = source.get('domain', '')
            if domain:
                domain_counts[domain] += 1
        
        # Get top domains (clusters)
        sorted_domains = sorted(
            domain_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return top 5 domains
        return [domain for domain, count in sorted_domains[:5]]
    
    def _identify_coverage_gaps(
        self,
        sources: List[Dict],
        query_analysis: Dict
    ) -> List[str]:
        """Identify potential gaps in source coverage"""
        gaps = []
        
        # Check for missing source types
        source_types = set(source.get('source_type', 'web') for source in sources)
        intent = query_analysis.get('intent', 'unknown')
        
        if intent == 'literature_review' and 'academic' not in source_types:
            gaps.append('academic sources')
        
        if intent == 'current_events' and 'news' not in source_types:
            gaps.append('news sources')
        
        # Check for missing search terms in sources
        search_terms = set(query_analysis.get('search_terms', []))
        covered_terms = set()
        
        for source in sources:
            url = (source.get('url') or '').lower()
            title = (source.get('metadata', {}).get('title_extracted') or '').lower()
            
            for term in search_terms:
                if term in url or term in title:
                    covered_terms.add(term)
        
        missing_terms = search_terms - covered_terms
        if missing_terms:
            gaps.append(f"coverage for terms: {', '.join(missing_terms)}")
        
        # Check for temporal coverage
        temporal_req = query_analysis.get('temporal_requirement', 'any')
        if temporal_req == 'recent':
            recent_sources = [
                s for s in sources
                if s.get('estimated_freshness') and 
                self._is_recent(s.get('estimated_freshness'))
            ]
            if len(recent_sources) < len(sources) * 0.5:
                gaps.append('recent sources')
        
        return gaps
    
    def _is_recent(self, date_str: str) -> bool:
        """Check if a date is recent (within last year)"""
        try:
            from datetime import datetime, timedelta
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            one_year_ago = datetime.now() - timedelta(days=365)
            return date >= one_year_ago
        except Exception:
            return False
    
    def _calculate_confidence_level(
        self,
        sources: List[Dict],
        query_analysis: Dict
    ) -> float:
        """Calculate overall confidence level in source selection"""
        if not sources:
            return 0.0
        
        # Factor 1: Average credibility
        avg_credibility = sum(s.get('credibility_score', 0) for s in sources) / len(sources)
        
        # Factor 2: Diversity (number of different domains)
        unique_domains = len(set(s.get('domain', '') for s in sources))
        diversity_score = min(1.0, unique_domains / 10.0)  # Target 10 unique domains
        
        # Factor 3: Coverage (how many search terms are covered)
        search_terms = set(query_analysis.get('search_terms', []))
        if search_terms:
            covered_terms = set()
            for source in sources:
                url = (source.get('url') or '').lower()
                for term in search_terms:
                    if term in url:
                        covered_terms.add(term)
            coverage_score = len(covered_terms) / len(search_terms)
        else:
            coverage_score = 0.5
        
        # Weighted combination
        confidence = (
            0.5 * avg_credibility +
            0.25 * diversity_score +
            0.25 * coverage_score
        )
        
        return min(1.0, confidence)
    
    def _calculate_overall_diversity(self, sources: List[Dict]) -> float:
        """Calculate overall diversity metric for sources"""
        if not sources:
            return 0.0
        
        # Count unique domains and source types
        unique_domains = len(set(s.get('domain', '') for s in sources))
        unique_types = len(set(s.get('source_type', 'web') for s in sources))
        
        # Normalize (target: 10 domains, 3 types)
        domain_diversity = min(1.0, unique_domains / 10.0)
        type_diversity = min(1.0, unique_types / 3.0)
        
        return (domain_diversity + type_diversity) / 2.0