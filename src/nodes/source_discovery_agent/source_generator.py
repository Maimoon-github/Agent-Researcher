"""
Source Generator - Phase 2: Source generation and discovery
"""

from typing import List, Dict, Optional, Set
import logging
from urllib.parse import quote_plus


class SourceGenerator:
    """Generates potential sources based on query analysis"""
    
    # Known authority domains by category
    ACADEMIC_DOMAINS = [
        'scholar.google.com', 'arxiv.org', 'pubmed.ncbi.nlm.nih.gov', 'ieee.org', 
        'jstor.org', 'researchgate.net', 'academia.edu', 'sciencedirect.com', 
        'springer.com', 'nature.com', 'science.org', 'thelancet.com', 
        'cell.com', 'nejm.org', 'pnas.org', 'plos.org', 'mit.edu', 
        'stanford.edu', 'harvard.edu', 'ox.ac.uk', 'cam.ac.uk'
    ]
    
    GOVERNMENT_DOMAINS = [
        'gov', 'nasa.gov', 'cdc.gov', 'nih.gov', 'data.gov', 'usa.gov', 
        'whitehouse.gov', 'epa.gov', 'noaa.gov', 'who.int', 'un.org', 
        'worldbank.org', 'imf.org', 'unesco.org', 'fao.org'
    ]
    
    NEWS_DOMAINS = [
        'reuters.com', 'apnews.com', 'bbc.com', 'nytimes.com', 'washingtonpost.com', 
        'theguardian.com', 'wsj.com', 'bloomberg.com', 'npr.org', 'aljazeera.com', 
        'economist.com', 'ft.com', 'cnn.com', 'forbes.com', 'time.com'
    ]
    
    TECHNICAL_DOMAINS = [
        'github.com', 'stackoverflow.com', 'developer.mozilla.org', 'docs.python.org', 
        'kubernetes.io', 'docker.com', 'aws.amazon.com', 'cloud.google.com', 
        'azure.microsoft.com', 'git-scm.com', 'npmjs.com', 'pypi.org', 
        'terraform.io', 'ansible.com'
    ]
    
    GENERAL_DOMAINS = [
        'wikipedia.org', 'britannica.com', 'medium.com', 'quora.com', 
        'reddit.com', 'stackexchange.com', 'ted.com', 'khanacademy.org', 
        'wolframalpha.com', 'investopedia.com', 'howstuffworks.com', 
        'wikihow.com', 'wired.com', 'theverge.com', 'technologyreview.com',
        'scientificamerican.com', 'nationalgeographic.com', 'history.com',
        'biography.com', 'thoughtco.com'
    ]
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_sources(
        self,
        query_analysis: Dict,
        source_type_preferences: Optional[List[str]] = None,
        max_sources_per_type: int = 10
    ) -> List[Dict]:
        """
        Generate potential sources based on query analysis
        
        Args:
            query_analysis: Results from QueryAnalyzer
            source_type_preferences: Preferred source types
            max_sources_per_type: Maximum sources per type
            
        Returns:
            List of potential source dictionaries
        """
        sources = []
        source_type_preferences = source_type_preferences or ['web', 'academic']
        
        # Extract key information from query analysis
        search_terms = query_analysis.get('search_terms', [])
        intent = query_analysis.get('intent', 'unknown')
        authority_level = query_analysis.get('authority_level', 'medium')
        domain_hints = query_analysis.get('domain_hints', {})
        
        # Generate web sources
        if 'web' in source_type_preferences:
            web_sources = self._generate_web_sources(
                search_terms,
                intent,
                domain_hints,
                authority_level,
                max_sources_per_type
            )
            sources.extend(web_sources)
        
        # Generate academic sources
        if 'academic' in source_type_preferences or domain_hints.get('academic'):
            academic_sources = self._generate_academic_sources(
                search_terms,
                max_sources_per_type
            )
            sources.extend(academic_sources)
        
        # Generate news sources
        if 'news' in source_type_preferences or intent == 'current_events':
            news_sources = self._generate_news_sources(
                search_terms,
                max_sources_per_type
            )
            sources.extend(news_sources)
        
        # Generate technical sources
        if domain_hints.get('technical') or domain_hints.get('agent'):
            tech_sources = self._generate_technical_sources(
                search_terms,
                max_sources_per_type
            )
            sources.extend(tech_sources)

        # Generate agent-specific sources
        if domain_hints.get('agent'):
            agent_sources = self._generate_agent_sources(
                search_terms,
                max_sources_per_type
            )
            sources.extend(agent_sources)
        
        self.logger.info(f"Generated {len(sources)} potential sources")
        
        return sources
    
    def _generate_web_sources(
        self,
        search_terms: List[str],
        intent: str,
        domain_hints: Dict,
        authority_level: str,
        max_sources: int
    ) -> List[Dict]:
        """Generate general web sources - extremely high yield strategy"""
        sources = []
        
        # Construct search query
        query = ' '.join(search_terms)
        encoded_query = quote_plus(query)
        
        # Always combine all domain groups for maximum possible yield to ensure 20+ resources
        all_domains = (
            self.ACADEMIC_DOMAINS + 
            self.GOVERNMENT_DOMAINS + 
            self.TECHNICAL_DOMAINS + 
            self.NEWS_DOMAINS + 
            self.GENERAL_DOMAINS
        )
            
        # Deduplicate domains while preserving order
        seen = set()
        domains = [d for d in all_domains if not (d in seen or seen.add(d))]
        
        # Generate URLs for domains (up to max_sources)
        for domain in domains[:max_sources]:
            sources.append({
                'url': f"https://{domain}/search?q={encoded_query}",
                'domain': domain,
                'source_type': 'web',
                'estimated_authority': authority_level,
                'generation_method': 'domain_pattern'
            })
        
        return sources
    
    def _generate_academic_sources(
        self,
        search_terms: List[str],
        max_sources: int
    ) -> List[Dict]:
        """Generate academic sources"""
        sources = []
        query = ' '.join(search_terms)
        encoded_query = quote_plus(query)
        
        # Academic-specific URLs
        academic_urls = [
            {
                'url': f"https://scholar.google.com/scholar?q={encoded_query}",
                'domain': 'scholar.google.com',
                'source_type': 'academic',
                'generation_method': 'academic_search'
            },
            {
                'url': f"https://arxiv.org/search/?query={encoded_query}",
                'domain': 'arxiv.org',
                'source_type': 'academic',
                'generation_method': 'preprint_server'
            },
            {
                'url': f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_query}",
                'domain': 'pubmed.ncbi.nlm.nih.gov',
                'source_type': 'academic',
                'generation_method': 'medical_database'
            },
        ]
        
        sources.extend(academic_urls[:max_sources])
        
        return sources
    
    def _generate_news_sources(
        self,
        search_terms: List[str],
        max_sources: int
    ) -> List[Dict]:
        """Generate news sources"""
        sources = []
        query = ' '.join(search_terms)
        encoded_query = quote_plus(query)
        
        # News domains
        for domain in self.NEWS_DOMAINS[:max_sources]:
            sources.append({
                'url': f"https://{domain}/search?q={encoded_query}",
                'domain': domain,
                'source_type': 'news',
                'generation_method': 'news_search'
            })
        
        return sources
    
    def _generate_technical_sources(
        self,
        search_terms: List[str],
        max_sources: int
    ) -> List[Dict]:
        """Generate technical documentation sources"""
        sources = []
        query = ' '.join(search_terms)
        encoded_query = quote_plus(query)
        
        # Technical-specific URLs
        tech_urls = [
            {
                'url': f"https://stackoverflow.com/search?q={encoded_query}",
                'domain': 'stackoverflow.com',
                'source_type': 'technical',
                'generation_method': 'qa_platform'
            },
            {
                'url': f"https://github.com/search?q={encoded_query}",
                'domain': 'github.com',
                'source_type': 'technical',
                'generation_method': 'code_repository'
            },
            {
                'url': f"https://developer.mozilla.org/en-US/search?q={encoded_query}",
                'domain': 'developer.mozilla.org',
                'source_type': 'technical',
                'generation_method': 'documentation'
            },
        ]
        
        sources.extend(tech_urls[:max_sources])
        
        return sources

    def _generate_agent_sources(
        self,
        search_terms: List[str],
        max_sources: int
    ) -> List[Dict]:
        """Generate sources specifically related to AI agents or this researcher"""
        sources = []
        
        # Add "Agent Researcher" if not strongly represented
        query_terms = list(search_terms)
        if not any('agent' in t.lower() for t in query_terms):
            query_terms.append('AI Agent')
            
        query = ' '.join(query_terms)
        encoded_query = quote_plus(query)
        
        # Specialized agent research domains
        agent_urls = [
            {
                'url': f"https://langchain.com/search?q={encoded_query}",
                'domain': 'langchain.com',
                'source_type': 'technical',
                'generation_method': 'framework_docs'
            },
            {
                'url': f"https://blog.langchain.dev/search?q={encoded_query}",
                'domain': 'blog.langchain.dev',
                'source_type': 'technical',
                'generation_method': 'framework_blog'
            },
            {
                'url': f"https://openai.com/search?q={encoded_query}",
                'domain': 'openai.com',
                'source_type': 'technical',
                'generation_method': 'ai_provider'
            },
            {
                'url': f"https://anthropic.com/search?q={encoded_query}",
                'domain': 'anthropic.com',
                'source_type': 'technical',
                'generation_method': 'ai_provider'
            }
        ]
        
        sources.extend(agent_urls[:max_sources])
        return sources

    def expand_query(self, search_terms: List[str]) -> List[str]:
        """
        Expand query with synonyms and related terms
        
        Args:
            search_terms: Original search terms
            
        Returns:
            Expanded list of search terms
        """
        # Simple synonym expansion (in production, use WordNet or word embeddings)
        synonym_map = {
            'impact': ['effect', 'influence', 'consequence'],
            'climate': ['weather', 'environment', 'atmospheric'],
            'change': ['alteration', 'transformation', 'shift'],
            'research': ['study', 'investigation', 'analysis'],
            'data': ['information', 'statistics', 'metrics'],
        }
        
        expanded_terms = list(search_terms)
        
        for term in search_terms:
            if term in synonym_map:
                expanded_terms.extend(synonym_map[term])
        
        # Remove duplicates while preserving order
        seen: Set[str] = set()
        unique_terms = []
        for term in expanded_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        return unique_terms
    
    def generate_url_patterns(self, domain: str, search_terms: List[str]) -> List[str]:
        """
        Generate URL patterns for a specific domain
        
        Args:
            domain: The domain to generate patterns for
            search_terms: Search terms to incorporate
            
        Returns:
            List of URL patterns
        """
        query = ' '.join(search_terms)
        encoded_query = quote_plus(query)
        
        # Common URL patterns
        patterns = [
            f"https://{domain}/search?q={encoded_query}",
            f"https://{domain}/s/{encoded_query}",
            f"https://{domain}/q/{encoded_query}",
            f"https://{domain}/?s={encoded_query}",
        ]
        
        return patterns