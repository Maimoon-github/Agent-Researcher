"""
Web Scraper Engine - Main orchestrator for web scraping operations
"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse
import uuid
import requests
from collections import defaultdict

from .config import get_domain_rules
from .utils import RobotsParser, URLNormalizer, ContentCleaner, LinkAnalyzer
from .extractors import NewspaperExtractor, ReadabilityExtractor, CustomExtractor, PDFExtractor
from .middlewares import AdaptiveRateLimiter, UserAgentMiddleware, CacheMiddleware, ProxyRotationManager
from .pipelines import ContentPipeline, ValidationPipeline


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebScraperEngine:
    """
    Main Web Scraper Engine
    
    Orchestrates the entire web scraping process:
    - Preparation & resource allocation
    - Intelligent scraping execution
    - Content processing & enhancement
    - Link discovery & expansion
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Web Scraper Engine
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or self._get_default_config()
        
        # Initialize components
        self.robots_parser = RobotsParser()
        self.url_normalizer = URLNormalizer()
        self.content_cleaner = ContentCleaner(
            preserve_structure=self.config.get('preserve_structure', True)
        )
        
        # Initialize middlewares
        self.rate_limiter = AdaptiveRateLimiter(
            default_delay=self.config.get('default_delay_seconds', 1.0)
        )
        self.user_agent_middleware = UserAgentMiddleware(
            user_agents=self.config.get('user_agents')
        )
        self.cache_middleware = CacheMiddleware(
            cache_dir=self.config.get('cache_storage_path', 'data/cache/web_scraper'),
            ttl_hours=self.config.get('cache_ttl_hours', 24)
        ) if self.config.get('enable_caching') else None
        
        # Initialize proxy manager if enabled
        self.proxy_manager = None
        if self.config.get('enable_proxy_rotation'):
            proxy_list = self._load_proxy_list()
            if proxy_list:
                self.proxy_manager = ProxyRotationManager(proxy_list)
        
        # Initialize extractors
        self.newspaper_extractor = NewspaperExtractor()
        self.readability_extractor = ReadabilityExtractor()
        self.pdf_extractor = PDFExtractor()
        
        # Initialize pipelines
        self.content_pipeline = ContentPipeline(
            preserve_structure=self.config.get('preserve_structure', True)
        )
        self.validation_pipeline = ValidationPipeline(
            min_content_length=self.config.get('min_content_length_chars', 100),
            max_content_length=self.config.get('max_content_length_chars', 100000)
        )
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_bytes_downloaded': 0
        }
        
        logger.info("Web Scraper Engine initialized")
    
    def scrape_urls(
        self,
        url_batch: List[Dict],
        batch_id: Optional[str] = None,
        priority_level: int = 3,
        extraction_patterns: Optional[Dict] = None
    ) -> Dict:
        """
        Main entry point: Scrape a batch of URLs
        
        Args:
            url_batch: List of URL dictionaries with metadata
            batch_id: Unique batch identifier
            priority_level: Priority level (1=high, 5=low)
            extraction_patterns: Custom extraction patterns (optional)
            
        Returns:
            Dictionary with scraping results
        """
        batch_id = batch_id or str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting batch {batch_id} with {len(url_batch)} URLs")
        
        # Phase 1: Preparation & Resource Allocation
        prepared_batch = self._prepare_batch(url_batch, extraction_patterns)
        
        # Phase 2: Intelligent Scraping Execution
        scraped_data = self._execute_scraping(prepared_batch)
        
        # Phase 3: Content Processing & Enhancement
        processed_data = self._process_content(scraped_data)
        
        # Phase 4: Link Discovery & Expansion
        discovered_links = self._discover_links(processed_data)
        
        # Compile results
        processing_time_ms = int((time.time() - start_time) * 1000)
        result = self._compile_results(
            batch_id=batch_id,
            scraped_data=processed_data,
            discovered_links=discovered_links,
            processing_time_ms=processing_time_ms
        )
        
        logger.info(f"Batch {batch_id} completed in {processing_time_ms}ms")
        
        return result
    
    def _prepare_batch(
        self,
        url_batch: List[Dict],
        extraction_patterns: Optional[Dict]
    ) -> List[Dict]:
        """
        Phase 1: Preparation & Resource Allocation
        """
        logger.debug("Phase 1: Preparing batch")
        
        prepared = []
        
        # Group URLs by domain
        domain_groups = defaultdict(list)
        for url_item in url_batch:
            url = url_item['url']
            domain = self.url_normalizer.get_domain(url)
            if domain:
                domain_groups[domain].append(url_item)
        
        # Process each domain group
        for domain, urls in domain_groups.items():
            # Get domain-specific rules
            domain_rules = get_domain_rules(domain)
            
            # Set domain-specific rate limit
            if 'rate_limit' in domain_rules:
                self.rate_limiter.set_domain_delay(domain, domain_rules['rate_limit'])
            
            # Prepare each URL
            for url_item in urls:
                url = url_item['url']
                
                # Normalize URL
                normalized_url = self.url_normalizer.normalize(url)
                if not normalized_url:
                    logger.warning(f"Skipping invalid URL: {url}")
                    continue
                
                # Check robots.txt
                if not self.robots_parser.can_fetch(normalized_url):
                    logger.warning(f"Robots.txt disallows: {normalized_url}")
                    continue
                
                # Add to prepared batch
                prepared_item = {
                    **url_item,
                    'normalized_url': normalized_url,
                    'domain': domain,
                    'domain_rules': domain_rules,
                    'extraction_patterns': extraction_patterns or domain_rules.get('extraction_patterns', {})
                }
                prepared.append(prepared_item)
        
        logger.debug(f"Prepared {len(prepared)} URLs for scraping")
        return prepared
    
    def _execute_scraping(self, prepared_batch: List[Dict]) -> List[Dict]:
        """
        Phase 2: Intelligent Scraping Execution
        """
        logger.debug("Phase 2: Executing scraping")
        
        results = []
        
        for item in prepared_batch:
            url = item['normalized_url']
            domain = item['domain']
            
            # Check cache first
            if self.cache_middleware:
                cached = self.cache_middleware.get(url)
                if cached:
                    logger.debug(f"Cache hit for {url}")
                    self.stats['cache_hits'] += 1
                    cached['scraping_metadata'] = cached.get('scraping_metadata', {})
                    cached['scraping_metadata']['cache_hit'] = True
                    results.append(cached)
                    continue
                else:
                    self.stats['cache_misses'] += 1
            
            # Rate limiting
            self.rate_limiter.wait_if_needed(domain)
            
            # Scrape URL
            scraped = self._scrape_single_url(item)
            
            if scraped:
                results.append(scraped)
                
                # Cache successful result
                if self.cache_middleware:
                    self.cache_middleware.set(url, scraped)
        
        logger.debug(f"Successfully scraped {len(results)} URLs")
        return results
    
    def _scrape_single_url(self, item: Dict) -> Optional[Dict]:
        """Scrape a single URL"""
        url = item['normalized_url']
        domain = item['domain']
        domain_rules = item['domain_rules']
        extraction_patterns = item['extraction_patterns']
        
        start_time = time.time()
        
        try:
            self.stats['total_requests'] += 1
            
            # Build request headers
            headers = {
                'User-Agent': self.user_agent_middleware.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # Get proxy if available
            proxies = None
            if self.proxy_manager:
                proxy = self.proxy_manager.get_proxy(domain)
                if proxy:
                    proxies = {'http': proxy, 'https': proxy}
            
            # Make request
            response = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=30,
                allow_redirects=True
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Record metrics
            self.rate_limiter.record_response(domain, response_time_ms, response.ok)
            if proxies and self.proxy_manager:
                if response.ok:
                    self.proxy_manager.record_success(proxy)
                else:
                    self.proxy_manager.record_failure(proxy)
            
            if not response.ok:
                logger.warning(f"HTTP {response.status_code} for {url}")
                self.stats['failed_scrapes'] += 1
                return None
            
            # Get content
            html = response.text
            content_type = response.headers.get('Content-Type', '')
            
            # Update stats
            self.stats['total_bytes_downloaded'] += len(response.content)
            
            # Extract content
            extracted = self._extract_content(
                html=html,
                url=url,
                content_type=content_type,
                extraction_patterns=extraction_patterns
            )
            
            if not extracted:
                logger.warning(f"Content extraction failed for {url}")
                self.stats['failed_scrapes'] += 1
                return None
            
            # Build result
            result = {
                'source_url': item['url'],
                'final_url': response.url,
                'http_status': response.status_code,
                'content_type': content_type,
                'download_timestamp': datetime.now().isoformat(),
                'download_duration_ms': response_time_ms,
                'content_metrics': {
                    'raw_html_size_bytes': len(response.content),
                    'extracted_text_length': len(extracted.get('text', '')),
                    'encoding': response.encoding or 'utf-8'
                },
                'extracted_content': extracted,
                'scraping_metadata': {
                    'parser_used': extracted.get('parser_used', 'unknown'),
                    'extraction_confidence': extracted.get('extraction_confidence', 0.0),
                    'cache_hit': False
                }
            }
            
            self.stats['successful_scrapes'] += 1
            return result
            
        except requests.Timeout:
            logger.warning(f"Timeout for {url}")
            self.stats['failed_scrapes'] += 1
            return None
        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            self.stats['failed_scrapes'] += 1
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            self.stats['failed_scrapes'] += 1
            return None
    
    def _extract_content(
        self,
        html: str,
        url: str,
        content_type: str,
        extraction_patterns: Dict
    ) -> Optional[Dict]:
        """
        Extract content using multi-strategy approach
        """
        # Strategy priority order
        strategies = [
            ('custom_selectors', 0.8),
            ('newspaper3k', 0.7),
            ('readability', 0.6),
            ('fallback', 0.5)
        ]
        
        for strategy_name, confidence_threshold in strategies:
            try:
                extracted = None
                
                if strategy_name == 'custom_selectors' and extraction_patterns:
                    custom_extractor = CustomExtractor(extraction_patterns)
                    extracted = custom_extractor.extract(html, url)
                    if extracted:
                        extracted['parser_used'] = 'custom'
                
                elif strategy_name == 'newspaper3k':
                    extracted = self.newspaper_extractor.extract(url, html)
                    if extracted:
                        extracted['parser_used'] = 'newspaper3k'
                
                elif strategy_name == 'readability':
                    extracted = self.readability_extractor.extract(html, url)
                    if extracted:
                        extracted['parser_used'] = 'readability'
                
                elif strategy_name == 'fallback':
                    custom_extractor = CustomExtractor()
                    extracted = custom_extractor.extract(html, url)
                    if extracted:
                        extracted['parser_used'] = 'fallback'
                
                # Check if extraction is good enough
                if extracted and extracted.get('extraction_confidence', 0) >= confidence_threshold * 0.8:
                    return extracted
                    
            except Exception as e:
                logger.debug(f"Extraction strategy '{strategy_name}' failed: {e}")
                continue
        
        return None
    
    def _process_content(self, scraped_data: List[Dict]) -> List[Dict]:
        """
        Phase 3: Content Processing & Enhancement
        """
        logger.debug("Phase 3: Processing content")
        
        processed = []
        
        for item in scraped_data:
            try:
                # Process extracted content
                extracted_content = item.get('extracted_content', {})
                processed_content = self.content_pipeline.process(extracted_content)
                item['extracted_content'] = processed_content
                
                # Validate
                is_valid, errors = self.validation_pipeline.validate(processed_content)
                item['validation'] = {
                    'is_valid': is_valid,
                    'errors': errors
                }
                
                if is_valid:
                    processed.append(item)
                else:
                    logger.debug(f"Content validation failed for {item['source_url']}: {errors}")
                    
            except Exception as e:
                logger.error(f"Content processing error: {e}")
                continue
        
        logger.debug(f"Processed {len(processed)} valid items")
        return processed
    
    def _discover_links(self, processed_data: List[Dict]) -> List[Dict]:
        """
        Phase 4: Link Discovery & Expansion
        """
        if not self.config.get('discover_new_links', True):
            return []
        
        logger.debug("Phase 4: Discovering links")
        
        all_discovered_links = []
        
        for item in processed_data:
            try:
                html = item['extracted_content'].get('html', '')
                if not html:
                    continue
                
                url = item['final_url']
                link_analyzer = LinkAnalyzer(url)
                
                # Extract links
                links = link_analyzer.extract_links(
                    html,
                    filter_same_domain=self.config.get('same_domain_only', True),
                    exclude_navigation=True
                )
                
                # Add to result
                item['discovered_links'] = links[:50]  # Limit to first 50
                all_discovered_links.extend(links)
                
            except Exception as e:
                logger.error(f"Link discovery error: {e}")
                continue
        
        logger.debug(f"Discovered {len(all_discovered_links)} links")
        return all_discovered_links
    
    def _compile_results(
        self,
        batch_id: str,
        scraped_data: List[Dict],
        discovered_links: List[Dict],
        processing_time_ms: int
    ) -> Dict:
        """Compile final results"""
        
        # Calculate statistics
        domain_distribution = defaultdict(lambda: {'success': 0, 'failed': 0})
        total_bytes = 0
        
        for item in scraped_data:
            domain = self.url_normalizer.get_domain(item['source_url'])
            if domain:
                domain_distribution[domain]['success'] += 1
            total_bytes += item.get('content_metrics', {}).get('raw_html_size_bytes', 0)
        
        # Determine status
        total_processed = len(scraped_data)
        if total_processed == 0:
            status = "failure"
        else:
            status = "success"
        
        result = {
            'status': status,
            'batch_id': batch_id,
            'processing_time_ms': processing_time_ms,
            'data': {
                'scraped_data': scraped_data,
                'batch_statistics': {
                    'total_urls_processed': self.stats['total_requests'],
                    'successful_scrapes': self.stats['successful_scrapes'],
                    'failed_scrapes': self.stats['failed_scrapes'],
                    'total_data_extracted_bytes': total_bytes,
                    'domain_distribution': dict(domain_distribution)
                },
                'rate_limiting_report': self.rate_limiter.get_stats() if hasattr(self.rate_limiter, 'get_stats') else {}
            },
            'next_actions': {
                'discovered_links_count': len(discovered_links),
                'recommended_batch_size': min(50, len(discovered_links))
            }
        }
        
        # Add cache stats if available
        if self.cache_middleware:
            result['data']['cache_statistics'] = self.cache_middleware.get_stats()
        
        return result
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'default_delay_seconds': 1.0,
            'max_concurrent_requests': 10,
            'preserve_structure': True,
            'enable_caching': True,
            'cache_ttl_hours': 24,
            'cache_storage_path': 'data/cache/web_scraper',
            'min_content_length_chars': 100,
            'max_content_length_chars': 100000,
            'discover_new_links': True,
            'same_domain_only': True,
            'enable_proxy_rotation': False
        }
    
    def _load_proxy_list(self) -> List[str]:
        """Load proxy list from file"""
        proxy_file = self.config.get('proxy_list_file')
        if not proxy_file:
            return []
        
        try:
            with open(proxy_file, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(proxies)} proxies from {proxy_file}")
            return proxies
        except Exception as e:
            logger.error(f"Failed to load proxies: {e}")
            return []
    
    def get_metrics(self) -> Dict:
        """Get engine metrics"""
        return {
            'stats': self.stats,
            'rate_limiter': self.rate_limiter.get_stats() if hasattr(self.rate_limiter, 'get_stats') else {},
            'cache': self.cache_middleware.get_stats() if self.cache_middleware else {},
            'proxy': self.proxy_manager.get_stats() if self.proxy_manager else {}
        }