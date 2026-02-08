"""
Metrics collection and monitoring for Source Discovery Agent
"""

from typing import Dict, List, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass, field
import time
import statistics


@dataclass
class CredibilityDistribution:
    """Statistics for credibility score distribution"""
    min: float = 0.0
    max: float = 0.0
    average: float = 0.0
    median: float = 0.0
    
    @classmethod
    def from_scores(cls, scores: List[float]) -> "CredibilityDistribution":
        """Calculate distribution from list of scores"""
        if not scores:
            return cls()
        
        return cls(
            min=min(scores),
            max=max(scores),
            average=statistics.mean(scores),
            median=statistics.median(scores)
        )


@dataclass
class DiscoveryMetrics:
    """Metrics for source discovery process"""
    total_sources_considered: int = 0
    validated_sources_count: int = 0
    validation_failures: int = 0
    processing_time_ms: int = 0
    credibility_score_distribution: CredibilityDistribution = field(
        default_factory=CredibilityDistribution
    )


class MetricsCollector:
    """Collects and aggregates metrics for the Source Discovery Agent"""
    
    def __init__(self):
        self.processing_times: List[float] = []
        self.sources_discovered: int = 0
        self.sources_validated: int = 0
        self.credibility_scores: List[float] = []
        self.validation_failures: Counter = Counter()
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.robots_txt_checks: int = 0
        self.network_errors: int = 0
        self.domain_counts: Counter = Counter()
        self.query_count: int = 0
        
        # Timing context
        self._start_time: Optional[float] = None
    
    def start_timing(self) -> None:
        """Start timing a processing operation"""
        self._start_time = time.time()
    
    def stop_timing(self) -> float:
        """Stop timing and record the duration in milliseconds"""
        if self._start_time is None:
            return 0.0
        
        duration_ms = (time.time() - self._start_time) * 1000
        self.processing_times.append(duration_ms)
        self._start_time = None
        return duration_ms
    
    def record_source_discovered(self) -> None:
        """Record that a source was discovered"""
        self.sources_discovered += 1
    
    def record_source_validated(self, credibility_score: float) -> None:
        """Record that a source was validated"""
        self.sources_validated += 1
        self.credibility_scores.append(credibility_score)
    
    def record_validation_failure(self, reason: str) -> None:
        """Record a validation failure with reason"""
        self.validation_failures[reason] += 1
    
    def record_cache_hit(self) -> None:
        """Record a cache hit"""
        self.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss"""
        self.cache_misses += 1
    
    def record_robots_check(self) -> None:
        """Record a robots.txt check"""
        self.robots_txt_checks += 1
    
    def record_network_error(self) -> None:
        """Record a network error"""
        self.network_errors += 1
    
    def record_domain(self, domain: str) -> None:
        """Record a domain being processed"""
        self.domain_counts[domain] += 1
    
    def record_query(self) -> None:
        """Record a query being processed"""
        self.query_count += 1
    
    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total
    
    def get_validation_success_rate(self) -> float:
        """Calculate validation success rate"""
        total = self.sources_validated + sum(self.validation_failures.values())
        if total == 0:
            return 0.0
        return self.sources_validated / total
    
    def get_discovery_metrics(self, processing_time_ms: int) -> DiscoveryMetrics:
        """Get discovery metrics for current operation"""
        failures = sum(self.validation_failures.values())
        
        return DiscoveryMetrics(
            total_sources_considered=self.sources_discovered,
            validated_sources_count=self.sources_validated,
            validation_failures=failures,
            processing_time_ms=processing_time_ms,
            credibility_score_distribution=CredibilityDistribution.from_scores(
                self.credibility_scores
            )
        )
    
    def get_summary(self) -> Dict:
        """Get a summary of all collected metrics"""
        return {
            'query_count': self.query_count,
            'total_sources_discovered': self.sources_discovered,
            'total_sources_validated': self.sources_validated,
            'validation_success_rate': self.get_validation_success_rate(),
            'average_processing_time_ms': (
                statistics.mean(self.processing_times) 
                if self.processing_times else 0.0
            ),
            'cache_hit_rate': self.get_cache_hit_rate(),
            'robots_txt_checks': self.robots_txt_checks,
            'network_errors': self.network_errors,
            'validation_failure_reasons': dict(self.validation_failures),
            'top_domains': dict(self.domain_counts.most_common(10)),
            'credibility_distribution': (
                CredibilityDistribution.from_scores(self.credibility_scores).__dict__
                if self.credibility_scores else {}
            )
        }
    
    def reset(self) -> None:
        """Reset all metrics"""
        self.__init__()