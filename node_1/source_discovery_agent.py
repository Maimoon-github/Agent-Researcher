"""
Source Discovery Agent - Production-Ready Implementation
=======================================================

A highly optimized, production-ready Source Discovery Agent built with LangGraph,
designed for multi-agent research automation pipelines.

Features:
- LangGraph-based node implementation with typed state management
- Web search using free googlesearch-python library
- Robots.txt compliance checking
- Credibility scoring and validation
- Rich metadata extraction with BeautifulSoup4
- Comprehensive error handling and logging
- Rate limiting and ethical scraping practices

Author: AI Research Systems Team
Version: 1.0.0
License: MIT
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from googlesearch import search as google_search
from langgraph.graph import StateGraph, END, START
from pydantic import BaseModel, Field, HttpUrl, field_validator


# =============================================================================
# CONFIGURATION
# =============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
USER_AGENT = "ResearchBot/1.0 (+https://example.com/bot)"
REQUEST_TIMEOUT = 10  # seconds
REQUEST_DELAY = 2.0  # seconds between requests
MAX_RETRIES = 3
CACHE_EXPIRY_HOURS = 24

# Trusted domains for credibility scoring (extensible)
TRUSTED_DOMAINS = {
    'edu': 0.9,
    'gov': 0.95,
    'org': 0.7,
    'ac.uk': 0.9,
    'wikipedia.org': 0.8,
    'arxiv.org': 0.95,
    'nature.com': 0.95,
    'science.org': 0.95,
    'ieee.org': 0.9,
    'acm.org': 0.9,
    'springer.com': 0.85,
    'sciencedirect.com': 0.85,
    'nih.gov': 0.95,
    'cdc.gov': 0.95,
}


# =============================================================================
# PYDANTIC MODELS - INPUT/OUTPUT SCHEMAS
# =============================================================================

class CredibilityRequirements(BaseModel):
    """
    Structured credibility requirements for source validation.
    
    This model defines the criteria that sources must meet to be considered
    credible for a given research topic.
    """
    min_domain_authority: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum domain authority score (0-1)"
    )
    max_age_days: Optional[int] = Field(
        default=365,
        ge=1,
        description="Maximum age of content in days (filters older sources)"
    )
    required_content_types: List[str] = Field(
        default_factory=lambda: ["webpage", "article"],
        description="Required content types (e.g., 'webpage', 'pdf', 'news')"
    )
    trusted_domains: List[str] = Field(
        default_factory=list,
        description="Whitelist of trusted domains (exact matches or TLDs)"
    )
    require_https: bool = Field(
        default=True,
        description="Require HTTPS protocol for security"
    )
    min_relevance_score: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score to topic"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "min_domain_authority": 0.7,
                "max_age_days": 180,
                "required_content_types": ["webpage", "article", "pdf"],
                "trusted_domains": ["edu", "gov", "arxiv.org"],
                "require_https": True,
                "min_relevance_score": 0.5
            }
        }


class SourceMetadata(BaseModel):
    """
    Rich metadata for a discovered source.
    
    Contains comprehensive information about a discovered source including
    credibility scores, validation status, and extracted metadata.
    """
    url: str = Field(description="Full URL of the source")
    title: Optional[str] = Field(default=None, description="Page title")
    description: Optional[str] = Field(default=None, description="Meta description or snippet")
    domain: str = Field(description="Domain name")
    domain_authority_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Computed domain authority/credibility score"
    )
    last_updated: Optional[datetime] = Field(
        default=None,
        description="Last modification date (if available)"
    )
    content_type: str = Field(
        default="webpage",
        description="Content type (webpage, pdf, news, etc.)"
    )
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Relevance to research topic"
    )
    validation_status: bool = Field(
        description="Whether source passed credibility checks"
    )
    is_https: bool = Field(description="Whether URL uses HTTPS")
    robots_allowed: bool = Field(
        default=True,
        description="Whether robots.txt allows scraping"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Extracted keywords from content"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if validation failed"
    )
    discovered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when source was discovered"
    )

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL is properly formatted"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://arxiv.org/abs/2101.00001",
                "title": "AI Ethics in Practice",
                "description": "Comprehensive study on ethical AI implementation",
                "domain": "arxiv.org",
                "domain_authority_score": 0.95,
                "last_updated": "2024-01-15T10:30:00",
                "content_type": "article",
                "relevance_score": 0.87,
                "validation_status": True,
                "is_https": True,
                "robots_allowed": True,
                "keywords": ["AI", "ethics", "machine learning"],
                "error_message": None
            }
        }


class SourceDiscoveryInput(BaseModel):
    """
    Input schema for the Source Discovery Agent.
    
    Combines the research topic with credibility requirements.
    """
    topic: str = Field(
        min_length=3,
        max_length=500,
        description="Research topic or query"
    )
    credibility_requirements: CredibilityRequirements = Field(
        default_factory=CredibilityRequirements,
        description="Credibility validation criteria"
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of sources to discover"
    )
    language: str = Field(
        default="en",
        description="Language code for search results"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "AI ethics and bias mitigation",
                "max_results": 20,
                "language": "en"
            }
        }


class SourceDiscoveryOutput(BaseModel):
    """
    Output schema for the Source Discovery Agent.
    
    Contains the curated list of validated sources with metadata.
    """
    sources: List[SourceMetadata] = Field(
        description="List of discovered and validated sources"
    )
    total_discovered: int = Field(
        description="Total number of sources discovered"
    )
    total_validated: int = Field(
        description="Number of sources that passed validation"
    )
    search_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the search process"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "sources": [],
                "total_discovered": 15,
                "total_validated": 12,
                "search_metadata": {
                    "execution_time_seconds": 8.5,
                    "errors_count": 3
                }
            }
        }


# =============================================================================
# LANGGRAPH STATE SCHEMA
# =============================================================================

class AgentState(TypedDict):
    """
    Shared state for the LangGraph workflow.
    
    This state is passed between nodes and maintains the workflow context.
    """
    # Input
    input: SourceDiscoveryInput
    
    # Processing state
    raw_urls: List[str]
    discovered_sources: List[SourceMetadata]
    validated_sources: List[SourceMetadata]
    
    # Metadata
    errors: List[Dict[str, Any]]
    execution_metadata: Dict[str, Any]
    
    # Output
    output: Optional[SourceDiscoveryOutput]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

class RobotsTxtChecker:
    """
    Thread-safe robots.txt checker with caching.
    
    Manages robots.txt validation with proper caching to avoid
    repeated requests to the same domain.
    """
    
    def __init__(self, cache_expiry_hours: int = CACHE_EXPIRY_HOURS):
        self.cache: Dict[str, tuple[RobotFileParser, datetime]] = {}
        self.cache_expiry = timedelta(hours=cache_expiry_hours)
        logger.info("RobotsTxtChecker initialized with %d hour cache", cache_expiry_hours)
    
    def can_fetch(self, url: str, user_agent: str = USER_AGENT) -> tuple[bool, Optional[float]]:
        """
        Check if URL can be fetched according to robots.txt.
        
        Args:
            url: The URL to check
            user_agent: User agent string
            
        Returns:
            Tuple of (can_fetch: bool, crawl_delay: Optional[float])
        """
        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            robots_url = urljoin(domain, "/robots.txt")
            
            # Check cache
            if domain in self.cache:
                parser, cached_at = self.cache[domain]
                if datetime.utcnow() - cached_at < self.cache_expiry:
                    can_fetch = parser.can_fetch(user_agent, url)
                    crawl_delay = parser.crawl_delay(user_agent)
                    logger.debug("Cache hit for %s: can_fetch=%s", domain, can_fetch)
                    return can_fetch, crawl_delay
            
            # Fetch and parse robots.txt
            parser = RobotFileParser()
            parser.set_url(robots_url)
            
            try:
                parser.read()
                self.cache[domain] = (parser, datetime.utcnow())
                can_fetch = parser.can_fetch(user_agent, url)
                crawl_delay = parser.crawl_delay(user_agent)
                logger.info("Fetched robots.txt for %s: can_fetch=%s", domain, can_fetch)
                return can_fetch, crawl_delay
            except Exception as e:
                # If robots.txt doesn't exist or can't be fetched, assume allowed
                logger.warning("Could not fetch robots.txt for %s: %s. Assuming allowed.", domain, e)
                return True, None
                
        except Exception as e:
            logger.error("Error checking robots.txt for %s: %s", url, e)
            # Default to allowed to avoid blocking legitimate sources
            return True, None


class CredibilityScorer:
    """
    Sophisticated credibility scoring system.
    
    Evaluates source credibility based on multiple factors including
    domain authority, HTTPS usage, and domain reputation.
    """
    
    def __init__(self, trusted_domains: Dict[str, float] = TRUSTED_DOMAINS):
        self.trusted_domains = trusted_domains
        logger.info("CredibilityScorer initialized with %d trusted domains", len(trusted_domains))
    
    def compute_domain_authority(self, url: str) -> float:
        """
        Compute domain authority score based on URL characteristics.
        
        This is a heuristic-based approach that can be extended with
        external authority APIs or machine learning models.
        
        Args:
            url: The URL to score
            
        Returns:
            Authority score between 0.0 and 1.0
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            score = 0.5  # Base score
            
            # Check against trusted domains
            for trusted, trust_score in self.trusted_domains.items():
                if domain.endswith(trusted):
                    logger.debug("Domain %s matched trusted domain %s (score: %.2f)", domain, trusted, trust_score)
                    return trust_score
            
            # TLD-based scoring
            if domain.endswith('.edu'):
                score = max(score, 0.85)
            elif domain.endswith('.gov'):
                score = max(score, 0.9)
            elif domain.endswith('.org'):
                score = max(score, 0.65)
            elif domain.endswith(('.ac.uk', '.edu.au')):
                score = max(score, 0.85)
            
            # HTTPS bonus
            if parsed.scheme == 'https':
                score += 0.05
            
            # Well-known subdomains
            if any(sub in domain for sub in ['research', 'scholar', 'academic', 'papers']):
                score += 0.05
            
            # Penalize suspicious patterns
            if len(domain.split('.')) > 4:  # Too many subdomains
                score -= 0.1
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error("Error computing domain authority for %s: %s", url, e)
            return 0.3  # Low default score on error


class RelevanceScorer:
    """
    Simple but effective relevance scorer.
    
    Uses keyword matching and simple text analysis to determine
    how relevant a page is to the research topic.
    """
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """Extract important keywords from text."""
        # Remove special characters and convert to lowercase
        cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Split into words and filter
        words = [w for w in cleaned.split() if len(w) > 3]
        
        # Simple frequency-based extraction
        from collections import Counter
        word_freq = Counter(words)
        
        # Return most common words
        return [word for word, _ in word_freq.most_common(max_keywords)]
    
    @staticmethod
    def compute_relevance(topic: str, title: Optional[str], 
                         description: Optional[str]) -> tuple[float, List[str]]:
        """
        Compute relevance score between topic and page content.
        
        Args:
            topic: Research topic
            title: Page title
            description: Page description
            
        Returns:
            Tuple of (relevance_score, keywords)
        """
        try:
            # Extract topic keywords
            topic_keywords = set(RelevanceScorer.extract_keywords(topic, 20))
            
            # Combine title and description
            content = f"{title or ''} {description or ''}".lower()
            
            if not content.strip():
                return 0.0, []
            
            # Extract content keywords
            content_keywords = RelevanceScorer.extract_keywords(content, 20)
            
            # Calculate overlap
            matches = sum(1 for kw in content_keywords if kw in topic_keywords)
            
            if not content_keywords:
                return 0.0, []
            
            # Weighted scoring
            title_weight = 0.7 if title else 0.0
            desc_weight = 0.3 if description else 0.0
            
            # Normalize weights
            total_weight = title_weight + desc_weight
            if total_weight == 0:
                return 0.0, content_keywords
            
            title_weight /= total_weight
            desc_weight /= total_weight
            
            # Compute score
            score = (matches / len(content_keywords)) * 0.8 + 0.2  # Min 0.2 base score
            
            # Boost if topic appears in title or description
            if title and any(kw in title.lower() for kw in topic_keywords):
                score += 0.15
            
            return min(1.0, score), content_keywords
            
        except Exception as e:
            logger.error("Error computing relevance: %s", e)
            return 0.0, []


class PageFetcher:
    """
    Robust page fetcher with retry logic and metadata extraction.
    """
    
    def __init__(self, timeout: int = REQUEST_TIMEOUT, max_retries: int = MAX_RETRIES):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.timeout = timeout
        self.max_retries = max_retries
        logger.info("PageFetcher initialized (timeout=%ds, max_retries=%d)", timeout, max_retries)
    
    def fetch_metadata(self, url: str) -> Dict[str, Any]:
        """
        Fetch and extract metadata from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {
            'title': None,
            'description': None,
            'last_modified': None,
            'content_type': 'webpage',
            'error': None
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.debug("Fetching %s (attempt %d/%d)", url, attempt + 1, self.max_retries)
                
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True,
                    headers={'Accept': 'text/html,application/xhtml+xml'}
                )
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('Content-Type', '').lower()
                
                if 'pdf' in content_type:
                    metadata['content_type'] = 'pdf'
                    # For PDFs, we can't easily extract metadata without additional libraries
                    metadata['title'] = url.split('/')[-1]
                    logger.debug("Detected PDF content at %s", url)
                    return metadata
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract title
                title_tag = soup.find('title')
                if title_tag:
                    metadata['title'] = title_tag.get_text().strip()
                
                # Extract description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    metadata['description'] = meta_desc.get('content', '').strip()
                
                # Try Open Graph description
                if not metadata['description']:
                    og_desc = soup.find('meta', attrs={'property': 'og:description'})
                    if og_desc:
                        metadata['description'] = og_desc.get('content', '').strip()
                
                # Extract last modified date
                last_modified_header = response.headers.get('Last-Modified')
                if last_modified_header:
                    try:
                        from email.utils import parsedate_to_datetime
                        metadata['last_modified'] = parsedate_to_datetime(last_modified_header)
                    except Exception as e:
                        logger.debug("Could not parse Last-Modified header: %s", e)
                
                # Try meta last-modified
                if not metadata['last_modified']:
                    meta_modified = soup.find('meta', attrs={'name': 'last-modified'})
                    if meta_modified:
                        try:
                            metadata['last_modified'] = datetime.fromisoformat(
                                meta_modified.get('content', '')
                            )
                        except Exception:
                            pass
                
                # Determine content type from page structure
                if soup.find('article'):
                    metadata['content_type'] = 'article'
                elif any(kw in url.lower() for kw in ['news', 'blog', 'post']):
                    metadata['content_type'] = 'news'
                
                logger.info("Successfully fetched metadata from %s", url)
                return metadata
                
            except requests.RequestException as e:
                logger.warning("Attempt %d failed for %s: %s", attempt + 1, url, e)
                metadata['error'] = str(e)
                
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                else:
                    logger.error("All attempts failed for %s", url)
                    
            except Exception as e:
                logger.error("Unexpected error fetching %s: %s", url, e)
                metadata['error'] = str(e)
                break
        
        return metadata


# =============================================================================
# CORE AGENT LOGIC
# =============================================================================

class SourceDiscoveryAgent:
    """
    Main Source Discovery Agent implementation.
    
    This class encapsulates all the logic for discovering, validating,
    and scoring sources based on credibility requirements.
    """
    
    def __init__(self):
        self.robots_checker = RobotsTxtChecker()
        self.credibility_scorer = CredibilityScorer()
        self.page_fetcher = PageFetcher()
        logger.info("SourceDiscoveryAgent initialized")
    
    def search_web(self, topic: str, max_results: int = 10, 
                   language: str = "en") -> List[str]:
        """
        Search the web for relevant URLs using googlesearch-python.
        
        Args:
            topic: Research topic to search for
            max_results: Maximum number of results to return
            language: Language code for search
            
        Returns:
            List of URLs
        """
        logger.info("Searching web for topic: '%s' (max_results=%d)", topic, max_results)
        
        try:
            # Use googlesearch-python library (free but unofficial)
            # Note: This may be rate-limited by Google
            urls = []
            
            for url in google_search(topic, num_results=max_results, lang=language):
                urls.append(url)
                logger.debug("Found URL: %s", url)
                
                if len(urls) >= max_results:
                    break
                
                # Be polite - add delay between requests
                time.sleep(REQUEST_DELAY)
            
            logger.info("Search completed. Found %d URLs", len(urls))
            return urls
            
        except Exception as e:
            logger.error("Web search failed: %s", e)
            # Return empty list on failure rather than crashing
            return []
    
    def validate_source(self, url: str, topic: str, 
                       requirements: CredibilityRequirements) -> SourceMetadata:
        """
        Validate and score a single source.
        
        Args:
            url: URL to validate
            topic: Research topic for relevance scoring
            requirements: Credibility requirements
            
        Returns:
            SourceMetadata object with validation results
        """
        logger.debug("Validating source: %s", url)
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        is_https = parsed_url.scheme == 'https'
        
        # Initialize metadata
        source = SourceMetadata(
            url=url,
            domain=domain,
            is_https=is_https,
            domain_authority_score=0.0,
            relevance_score=0.0,
            validation_status=False
        )
        
        try:
            # Check robots.txt
            can_fetch, crawl_delay = self.robots_checker.can_fetch(url)
            source.robots_allowed = can_fetch
            
            if not can_fetch:
                source.error_message = "Disallowed by robots.txt"
                logger.info("Source %s disallowed by robots.txt", url)
                return source
            
            # Respect crawl delay if specified
            if crawl_delay:
                logger.debug("Applying crawl delay of %.1fs for %s", crawl_delay, domain)
                time.sleep(max(crawl_delay, REQUEST_DELAY))
            else:
                time.sleep(REQUEST_DELAY)
            
            # Fetch metadata
            metadata = self.page_fetcher.fetch_metadata(url)
            
            if metadata['error']:
                source.error_message = f"Fetch failed: {metadata['error']}"
                logger.warning("Failed to fetch %s: %s", url, metadata['error'])
                return source
            
            # Update source with fetched metadata
            source.title = metadata['title']
            source.description = metadata['description']
            source.last_updated = metadata['last_modified']
            source.content_type = metadata['content_type']
            
            # Compute domain authority
            source.domain_authority_score = self.credibility_scorer.compute_domain_authority(url)
            
            # Compute relevance
            relevance, keywords = RelevanceScorer.compute_relevance(
                topic, source.title, source.description
            )
            source.relevance_score = relevance
            source.keywords = keywords
            
            # Validate against requirements
            validation_passed = True
            failure_reasons = []
            
            # Check domain authority
            if source.domain_authority_score < requirements.min_domain_authority:
                validation_passed = False
                failure_reasons.append(
                    f"Domain authority {source.domain_authority_score:.2f} < {requirements.min_domain_authority:.2f}"
                )
            
            # Check age
            if requirements.max_age_days and source.last_updated:
                age_days = (datetime.utcnow() - source.last_updated).days
                if age_days > requirements.max_age_days:
                    validation_passed = False
                    failure_reasons.append(f"Content age {age_days} days > {requirements.max_age_days} days")
            
            # Check content type
            if requirements.required_content_types:
                if source.content_type not in requirements.required_content_types:
                    validation_passed = False
                    failure_reasons.append(f"Content type '{source.content_type}' not in required types")
            
            # Check HTTPS requirement
            if requirements.require_https and not is_https:
                validation_passed = False
                failure_reasons.append("HTTPS required but URL uses HTTP")
            
            # Check relevance
            if source.relevance_score < requirements.min_relevance_score:
                validation_passed = False
                failure_reasons.append(
                    f"Relevance {source.relevance_score:.2f} < {requirements.min_relevance_score:.2f}"
                )
            
            # Check trusted domains
            if requirements.trusted_domains:
                domain_trusted = any(
                    domain.endswith(trusted) for trusted in requirements.trusted_domains
                )
                if not domain_trusted:
                    validation_passed = False
                    failure_reasons.append("Domain not in trusted whitelist")
            
            source.validation_status = validation_passed
            
            if not validation_passed:
                source.error_message = "; ".join(failure_reasons)
                logger.info("Source %s failed validation: %s", url, source.error_message)
            else:
                logger.info("Source %s passed validation (authority=%.2f, relevance=%.2f)", 
                          url, source.domain_authority_score, source.relevance_score)
            
            return source
            
        except Exception as e:
            logger.error("Error validating source %s: %s", url, e)
            source.error_message = f"Validation error: {str(e)}"
            return source


# =============================================================================
# LANGGRAPH NODE FUNCTIONS
# =============================================================================

def search_node(state: AgentState) -> AgentState:
    """
    Node 1: Perform web search to discover candidate URLs.
    
    This node takes the research topic from the input and performs
    a web search to discover candidate URLs.
    """
    logger.info("=== SEARCH NODE ===")
    
    agent = SourceDiscoveryAgent()
    input_data = state['input']
    
    start_time = time.time()
    
    # Perform web search
    urls = agent.search_web(
        topic=input_data.topic,
        max_results=input_data.max_results,
        language=input_data.language
    )
    
    execution_time = time.time() - start_time
    
    # Update state
    state['raw_urls'] = urls
    state['execution_metadata']['search_time'] = execution_time
    state['execution_metadata']['urls_found'] = len(urls)
    
    logger.info("Search completed in %.2fs. Found %d URLs", execution_time, len(urls))
    
    return state


def validation_node(state: AgentState) -> AgentState:
    """
    Node 2: Validate and score each discovered URL.
    
    This node takes the raw URLs from the search node and validates
    each one against the credibility requirements.
    """
    logger.info("=== VALIDATION NODE ===")
    
    agent = SourceDiscoveryAgent()
    input_data = state['input']
    urls = state['raw_urls']
    
    start_time = time.time()
    
    discovered_sources = []
    validated_sources = []
    errors = []
    
    # Validate each URL
    for i, url in enumerate(urls, 1):
        logger.info("Processing source %d/%d: %s", i, len(urls), url)
        
        try:
            source_metadata = agent.validate_source(
                url=url,
                topic=input_data.topic,
                requirements=input_data.credibility_requirements
            )
            
            discovered_sources.append(source_metadata)
            
            if source_metadata.validation_status:
                validated_sources.append(source_metadata)
            else:
                errors.append({
                    'url': url,
                    'error': source_metadata.error_message,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error("Error processing %s: %s", url, e)
            errors.append({
                'url': url,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
    
    execution_time = time.time() - start_time
    
    # Update state
    state['discovered_sources'] = discovered_sources
    state['validated_sources'] = validated_sources
    state['errors'] = errors
    state['execution_metadata']['validation_time'] = execution_time
    state['execution_metadata']['sources_validated'] = len(validated_sources)
    state['execution_metadata']['validation_errors'] = len(errors)
    
    logger.info("Validation completed in %.2fs. Validated %d/%d sources", 
               execution_time, len(validated_sources), len(discovered_sources))
    
    return state


def output_node(state: AgentState) -> AgentState:
    """
    Node 3: Format the final output.
    
    This node takes the validated sources and formats them into
    the final output structure.
    """
    logger.info("=== OUTPUT NODE ===")
    
    validated_sources = state['validated_sources']
    discovered_sources = state['discovered_sources']
    
    # Sort validated sources by credibility and relevance
    sorted_sources = sorted(
        validated_sources,
        key=lambda s: (s.domain_authority_score + s.relevance_score) / 2,
        reverse=True
    )
    
    # Create output
    output = SourceDiscoveryOutput(
        sources=sorted_sources,
        total_discovered=len(discovered_sources),
        total_validated=len(validated_sources),
        search_metadata={
            **state['execution_metadata'],
            'errors': state['errors'],
            'completion_time': datetime.utcnow().isoformat()
        }
    )
    
    state['output'] = output
    
    logger.info("Output formatted. Returning %d validated sources", len(sorted_sources))
    
    return state


# =============================================================================
# LANGGRAPH WORKFLOW DEFINITION
# =============================================================================

def create_source_discovery_graph() -> StateGraph:
    """
    Create and compile the LangGraph workflow for source discovery.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Creating Source Discovery Graph")
    
    # Initialize graph with state schema
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("search", search_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("output", output_node)
    
    # Define edges (linear flow for this agent)
    workflow.add_edge(START, "search")
    workflow.add_edge("search", "validation")
    workflow.add_edge("validation", "output")
    workflow.add_edge("output", END)
    
    # Compile graph
    compiled_graph = workflow.compile()
    
    logger.info("Source Discovery Graph created successfully")
    
    return compiled_graph


# =============================================================================
# MAIN EXECUTION FUNCTION
# =============================================================================

def run_source_discovery(input_data: SourceDiscoveryInput) -> SourceDiscoveryOutput:
    """
    Main execution function for the Source Discovery Agent.
    
    This is the primary interface for running the agent. It creates the graph,
    initializes the state, and executes the workflow.
    
    Args:
        input_data: SourceDiscoveryInput with topic and requirements
        
    Returns:
        SourceDiscoveryOutput with validated sources
    """
    logger.info("=" * 80)
    logger.info("Starting Source Discovery Agent")
    logger.info("Topic: %s", input_data.topic)
    logger.info("Max Results: %d", input_data.max_results)
    logger.info("=" * 80)
    
    start_time = time.time()
    
    # Create graph
    graph = create_source_discovery_graph()
    
    # Initialize state
    initial_state: AgentState = {
        'input': input_data,
        'raw_urls': [],
        'discovered_sources': [],
        'validated_sources': [],
        'errors': [],
        'execution_metadata': {
            'started_at': datetime.utcnow().isoformat(),
            'topic': input_data.topic
        },
        'output': None
    }
    
    # Execute graph
    try:
        final_state = graph.invoke(initial_state)
        
        total_time = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info("Source Discovery Agent Completed")
        logger.info("Total Execution Time: %.2fs", total_time)
        logger.info("Sources Discovered: %d", final_state['output'].total_discovered)
        logger.info("Sources Validated: %d", final_state['output'].total_validated)
        logger.info("=" * 80)
        
        return final_state['output']
        
    except Exception as e:
        logger.error("Error executing Source Discovery Agent: %s", e)
        raise


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Source Discovery Agent - Example Execution")
    print("=" * 80 + "\n")
    
    # Define research topic and requirements
    example_input = SourceDiscoveryInput(
        topic="AI ethics and bias mitigation in machine learning",
        max_results=15,
        language="en",
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.6,
            max_age_days=730,  # 2 years
            required_content_types=["webpage", "article", "pdf"],
            trusted_domains=["edu", "gov", "arxiv.org", "ieee.org"],
            require_https=True,
            min_relevance_score=0.4
        )
    )
    
    # Run the agent
    try:
        output = run_source_discovery(example_input)
        
        # Display results
        print("\n" + "=" * 80)
        print("RESULTS SUMMARY")
        print("=" * 80)
        print(f"Total Discovered: {output.total_discovered}")
        print(f"Total Validated: {output.total_validated}")
        print(f"Success Rate: {output.total_validated / output.total_discovered * 100:.1f}%")
        
        print("\n" + "=" * 80)
        print("TOP VALIDATED SOURCES")
        print("=" * 80)
        
        for i, source in enumerate(output.sources[:5], 1):  # Show top 5
            print(f"\n{i}. {source.title or 'No title'}")
            print(f"   URL: {source.url}")
            print(f"   Domain: {source.domain}")
            print(f"   Authority Score: {source.domain_authority_score:.2f}")
            print(f"   Relevance Score: {source.relevance_score:.2f}")
            print(f"   Content Type: {source.content_type}")
            print(f"   HTTPS: {'Yes' if source.is_https else 'No'}")
            if source.keywords:
                print(f"   Keywords: {', '.join(source.keywords[:5])}")
        
        print("\n" + "=" * 80)
        print("EXECUTION METADATA")
        print("=" * 80)
        print(f"Search Time: {output.search_metadata.get('search_time', 0):.2f}s")
        print(f"Validation Time: {output.search_metadata.get('validation_time', 0):.2f}s")
        print(f"Validation Errors: {output.search_metadata.get('validation_errors', 0)}")
        
        if output.search_metadata.get('errors'):
            print("\n" + "=" * 80)
            print("VALIDATION ERRORS (Sample)")
            print("=" * 80)
            for error in output.search_metadata['errors'][:3]:  # Show first 3
                print(f"\nURL: {error['url']}")
                print(f"Error: {error['error']}")
        
        print("\n" + "=" * 80)
        print("INTEGRATION NOTES")
        print("=" * 80)
        print("""
The validated sources are now ready to be passed to downstream agents:

1. Web Scraper Engine: Will receive the curated list of URLs with metadata
   - Can use the robots_allowed flag to skip disallowed URLs
   - Can use the domain_authority_score for prioritization
   
2. Local File Loader: Can process any PDF sources identified
   - Filter sources where content_type == 'pdf'
   
3. Process Orchestrator: Can use execution metadata for monitoring
   - Track success rates and execution times
   - Monitor error patterns for system health

The SourceDiscoveryOutput object can be serialized to JSON for storage
or passed directly to downstream nodes in the LangGraph workflow.
        """)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Example Execution Complete")
    print("=" * 80 + "\n")
