"""
Source Discovery Agent - Main orchestration class
"""

from typing import Dict, List, Optional
from urllib.parse import urlparse
import logging
from datetime import datetime
import uuid
from pathlib import Path
import asyncio

from .config import SourceDiscoveryConfig
from .exceptions import (
    NoSourcesFoundError,
    QueryValidationError,
    CredibilityThresholdError
)
from .query_analyzer import QueryAnalyzer
from .source_generator import SourceGenerator
from .validator import SourceValidator
from .credibility_scorer import CredibilityScorer
from .robots_parser import RobotsParser
from .local_discoverer import LocalFileDiscoverer
from .curator import SourceCurator
from .web_searcher import WebSearcher
from .metrics import MetricsCollector, DiscoveryMetrics


class SourceDiscoveryAgent:
    """
    Main Source Discovery Agent - orchestrates the entire discovery process
    """
    
    def __init__(
        self,
        config: Optional[SourceDiscoveryConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the Source Discovery Agent
        
        Args:
            config: Configuration object (uses defaults if not provided)
            logger: Logger instance (creates one if not provided)
        """
        self.config = config or SourceDiscoveryConfig()
        self.config.validate()
        
        self.logger = logger or self._setup_logger()
        
        # Initialize components
        self.query_analyzer = QueryAnalyzer(logger=self.logger)
        self.source_generator = SourceGenerator(logger=self.logger)
        self.validator = SourceValidator(
            timeout=self.config.request_timeout_seconds,
            user_agent=self.config.user_agent,
            logger=self.logger
        )
        self.credibility_scorer = CredibilityScorer(logger=self.logger)
        self.robots_parser = RobotsParser(
            user_agent=self.config.user_agent,
            cache_ttl_hours=self.config.cache_ttl_hours,
            request_timeout=self.config.request_timeout_seconds,
            logger=self.logger
        )
        self.local_discoverer = LocalFileDiscoverer(
            base_directories=self.config.local_scan_directories,
            supported_extensions=self.config.required_file_extensions,
            logger=self.logger
        )
        self.curator = SourceCurator(logger=self.logger)
        self.web_searcher = WebSearcher(
            timeout=self.config.request_timeout_seconds,
            user_agent=self.config.user_agent,
            logger=self.logger
        )
        
        # Metrics
        self.metrics = MetricsCollector()
        
        self.logger.info("Source Discovery Agent initialized")
    
    def discover_sources(
        self,
        query: str,
        query_id: Optional[str] = None,
        source_type_preferences: Optional[List[str]] = None,
        credibility_threshold: Optional[float] = None,
        max_sources_per_type: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        Main entry point: Discover sources for a research query
        
        Args:
            query: The research query string
            query_id: Optional UUID for tracking
            source_type_preferences: Preferred source types
            credibility_threshold: Minimum credibility score (overrides config)
            max_sources_per_type: Max sources per type (overrides config)
            **kwargs: Additional optional parameters
            
        Returns:
            Dictionary with discovered sources and metadata
        """
        # Start timing
        self.metrics.start_timing()
        self.metrics.record_query()
        
        # Generate query ID if not provided
        query_id = query_id or str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Use config defaults if not provided
        credibility_threshold = credibility_threshold or self.config.credibility_threshold
        max_sources_per_type = max_sources_per_type or self.config.max_sources_per_type
        
        self.logger.info(f"Processing query {query_id}: '{query}'")
        
        try:
            # Execute the core discovery logic asynchronously for rapid execution
            return asyncio.run(self._run_discovery_async(
                query,
                query_id,
                timestamp,
                source_type_preferences,
                credibility_threshold,
                max_sources_per_type
            ))
        except Exception as e:
            self.logger.exception(f"Fatal error during discovery: {e}")
            
            # Stop timing even on error
            processing_time = int(self.metrics.stop_timing())
            
            return self._build_error_response(
                query_id=query_id,
                timestamp=timestamp,
                error=e
            )
    
    async def _run_discovery_async(
        self,
        query: str,
        query_id: str,
        timestamp: str,
        source_type_preferences: Optional[List[str]],
        credibility_threshold: float,
        max_sources_per_type: int
    ) -> Dict:
        """Asynchronous orchestration of the discovery process"""
        # Validate query
        self._validate_query(query)
        
        # Phase 1: Query Analysis
        self.logger.info(f"Phase 1: Analyzing query {query_id}")
        query_analysis = self.query_analyzer.analyze(query)
        
        # Phase 2: Source Generation (Pattern-based + Live Search)
        self.logger.info(f"Phase 2: Generating sources for {query_id}")
        
        # Run pattern generation and live search concurrently
        gen_task = asyncio.to_thread(
            self.source_generator.generate_sources,
            query_analysis,
            source_type_preferences,
            max_sources_per_type
        )
        search_task = self.web_searcher.search_async(query, max_results=max_sources_per_type)
        
        potential_sources, live_results = await asyncio.gather(gen_task, search_task)
        
        if live_results:
            self.logger.info(f"Retrieved {len(live_results)} live search results")
            potential_sources.extend(live_results)
            
        # Phase 2.5: Local File Discovery (Async-friendly)
        if query_analysis.get('domain_hints', {}).get('agent'):
            project_root = str(Path(__file__).parent.parent.parent.parent.absolute())
            if project_root not in self.local_discoverer.base_directories:
                self.logger.info(f"Targeting agent query: Adding project root {project_root} to local scan")
                self.local_discoverer.base_directories.append(project_root)
        
        local_files = await asyncio.to_thread(self.local_discoverer.discover_files, query_analysis)
        
        if not potential_sources and not local_files:
            raise NoSourcesFoundError(f"No potential sources found for query: {query}")
            
        # Phase 3: Source Validation (Concurrent)
        self.logger.info(f"Phase 3: Validating {len(potential_sources)} sources (concurrently) for {query_id}")
        validated_sources = await self._validate_sources_async(
            potential_sources,
            credibility_threshold
        )
        
        if not validated_sources and not local_files:
            raise NoSourcesFoundError(
                f"No sources met validation criteria (threshold: {credibility_threshold})"
            )
            
        # Phase 4: Curation
        self.logger.info(f"Phase 4: Curating sources for {query_id}")
        curated_results = await asyncio.to_thread(
            self.curator.curate_sources,
            validated_sources,
            query_analysis,
            max_sources=max_sources_per_type
        )
        
        # Stop timing
        processing_time = int(self.metrics.stop_timing())
        
        # Build metrics and result
        discovery_metrics = self.metrics.get_discovery_metrics(processing_time)
        
        return self._build_success_response(
            query_id,
            timestamp,
            query_analysis,
            curated_results['ranked_sources'],
            local_files,
            curated_results,
            discovery_metrics
        )
    
    def _validate_query(self, query: str) -> None:
        """Validate query input"""
        if not query or not isinstance(query, str):
            raise QueryValidationError("Query must be a non-empty string")
        
        if len(query) < 3:
            raise QueryValidationError("Query must be at least 3 characters")
        
        if len(query) > 1000:
            raise QueryValidationError("Query must be less than 1000 characters")
    
    async def _validate_single_source_async(
        self,
        source: Dict,
        credibility_threshold: float
    ) -> Optional[Dict]:
        """Validate a single source asynchronously"""
        url = source.get('url')
        if not url:
            return None
            
        self.metrics.record_source_discovered()
        
        # 1. URL Syntax
        is_valid, error = self.validator.validate_url(url)
        if not is_valid:
            self.metrics.record_validation_failure("invalid_url")
            return None
            
        # 2. Robots.txt (Async)
        self.metrics.record_robots_check()
        if not await self.robots_parser.is_allowed_async(url):
            self.metrics.record_validation_failure("robots_disallowed")
            return None
            
        # 3. Reachability (Async)
        reachability = await self.validator.check_reachability_async(url)
        if not reachability['reachable']:
            self.metrics.record_validation_failure("unreachable")
            self.metrics.record_network_error()
            return None
            
        # 4. Credibility
        metadata = {
            'content_type': reachability.get('content_type'),
            'estimated_size_kb': reachability.get('estimated_size_kb'),
        }
        credibility_score = self.credibility_scorer.calculate_score(url, metadata)
        
        if credibility_score < credibility_threshold:
            self.metrics.record_validation_failure("low_credibility")
            return None
            
        # Passed!
        domain = urlparse(url).netloc
        self.metrics.record_domain(domain)
        self.metrics.record_source_validated(credibility_score)
        
        return {
            'url': url,
            'domain': domain,
            'credibility_score': credibility_score,
            'robots_allowed': True,
            'estimated_freshness': source.get('estimated_freshness'),
            'source_type': source.get('source_type', 'web'),
            'generation_method': source.get('generation_method', 'pattern'),
            'validation_timestamp': datetime.utcnow().isoformat() + 'Z',
            'metadata': {
                'title_extracted': source.get('title'),
                'snippet': source.get('snippet'),
                'content_type': metadata['content_type'],
                'estimated_size_kb': metadata['estimated_size_kb']
            }
        }

    async def _validate_sources_async(
        self,
        potential_sources: List[Dict],
        credibility_threshold: float
    ) -> List[Dict]:
        """Validate multiple sources concurrently using asyncio.gather"""
        tasks = [
            self._validate_single_source_async(source, credibility_threshold)
            for source in potential_sources
        ]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    def _validate_sources(
        self,
        potential_sources: List[Dict],
        credibility_threshold: float
    ) -> List[Dict]:
        """Synchronous wrapper for asynchronous source validation"""
        return asyncio.run(self._validate_sources_async(
            potential_sources,
            credibility_threshold
        ))
    
    def _build_success_response(
        self,
        query_id: str,
        timestamp: str,
        query_analysis: Dict,
        validated_sources: List[Dict],
        local_files: List[Dict],
        curated_results: Dict,
        discovery_metrics: DiscoveryMetrics
    ) -> Dict:
        """Build successful discovery response"""
        # Extract search terms
        search_terms = query_analysis.get('search_terms', [])
        
        # Prepare warnings
        warnings = []
        robots_failures = sum(
            1 for reason, count in self.metrics.validation_failures.items()
            if 'robots' in reason
        )
        if robots_failures > 0:
            warnings.append(f"{robots_failures} sources excluded due to robots.txt restrictions")
        
        if self.config.local_scan_directories and not local_files:
            warnings.append("Local file scan limited to configured directories")
        
        return {
            'status': 'success',
            'query_id': query_id,
            'processing_time_ms': discovery_metrics.processing_time_ms,
            'data': {
                'search_terms': search_terms,
                'validated_urls': validated_sources,
                'local_file_patterns': local_files,
                'source_types_identified': curated_results['source_types_identified'],
                'discovery_metrics': {
                    'total_sources_considered': discovery_metrics.total_sources_considered,
                    'validated_sources_count': discovery_metrics.validated_sources_count,
                    'validation_failures': discovery_metrics.validation_failures,
                    'processing_time_ms': discovery_metrics.processing_time_ms,
                    'credibility_score_distribution': {
                        'min': discovery_metrics.credibility_score_distribution.min,
                        'max': discovery_metrics.credibility_score_distribution.max,
                        'average': discovery_metrics.credibility_score_distribution.average,
                        'median': discovery_metrics.credibility_score_distribution.median,
                    }
                },
                'recommendations': {
                    'primary_source_clusters': curated_results['primary_source_clusters'],
                    'suggested_next_queries': [],  # Could implement query suggestions
                    'coverage_gaps': curated_results['coverage_gaps'],
                    'confidence_level': curated_results['confidence_level']
                }
            },
            'warnings': warnings,
            'timestamp': timestamp
        }
    
    def _build_error_response(
        self,
        query_id: str,
        timestamp: str,
        error: Exception
    ) -> Dict:
        """Build error response"""
        # Determine error type
        if isinstance(error, QueryValidationError):
            error_type = 'validation_error'
        elif isinstance(error, NoSourcesFoundError):
            error_type = 'no_sources_found'
        else:
            error_type = 'query_parsing_failed'
        
        # Generate suggestions
        suggestions = []
        if isinstance(error, CredibilityThresholdError):
            suggestions.append(f"Lower credibility threshold below {self.config.credibility_threshold}")
            suggestions.append("Expand search to include blog sources")
        elif isinstance(error, NoSourcesFoundError):
            suggestions.append("Try broader search terms")
            suggestions.append("Enable additional source types")
        
        return {
            'status': 'error',
            'query_id': query_id,
            'error': {
                'type': error_type,
                'code': error_type.upper(),
                'message': str(error),
                'details': {},
                'suggestions': suggestions,
                'fallback_actions': [
                    'Returning empty result set',
                    'Logging detailed failure analysis'
                ]
            },
            'timestamp': timestamp
        }
    
    def get_metrics(self) -> Dict:
        """Get current metrics summary"""
        return self.metrics.get_summary()
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.metrics.reset()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger('SourceDiscoveryAgent')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger