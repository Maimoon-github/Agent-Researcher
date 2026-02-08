"""
Configuration management for Source Discovery Agent
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import yaml
import os


@dataclass
class SourceWeights:
    """Weights for different source types"""
    academic: float = 1.2
    government: float = 1.3
    news: float = 1.0
    blog: float = 0.7
    forum: float = 0.5


@dataclass
class RecencyRequirements:
    """Recency requirements for sources"""
    max_age_days: Optional[int] = None
    prefer_fresh: bool = False


@dataclass
class SourceDiscoveryConfig:
    """Configuration for Source Discovery Agent"""
    
    # Validation parameters
    min_credibility_score: float = 0.5
    max_urls_per_domain: int = 5
    request_timeout_seconds: int = 10
    user_agent: str = "ResearchAgent/1.0 (Compatible; ResearchBot)"
    
    # Source type weights
    source_weights: SourceWeights = field(default_factory=SourceWeights)
    
    # Directory scanning
    local_scan_directories: List[str] = field(default_factory=list)
    
    # Blacklists/whitelists
    domain_blacklist: List[str] = field(default_factory=list)
    domain_whitelist: List[str] = field(default_factory=list)
    
    # Advanced features
    enable_wayback_check: bool = True
    enable_cross_referencing: bool = True
    cache_validation_results: bool = True
    cache_ttl_hours: int = 24
    
    # Processing limits
    max_sources_per_type: int = 60
    credibility_threshold: float = 0.5
    
    # File extensions
    required_file_extensions: List[str] = field(
        default_factory=lambda: ["pdf", "md", "txt", "docx"]
    )
    
    # Language filters
    language_filters: List[str] = field(default_factory=list)
    
    @classmethod
    def from_yaml(cls, filepath: str) -> "SourceDiscoveryConfig":
        """Load configuration from YAML file"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        
        # Extract source_discovery section if present
        config_data = data.get('source_discovery', data)
        
        # Handle nested source_weights
        if 'source_weights' in config_data:
            config_data['source_weights'] = SourceWeights(**config_data['source_weights'])
        
        return cls(**config_data)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SourceDiscoveryConfig":
        """Create configuration from dictionary"""
        if 'source_weights' in data and isinstance(data['source_weights'], dict):
            data['source_weights'] = SourceWeights(**data['source_weights'])
        return cls(**data)
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        result = {
            'min_credibility_score': self.min_credibility_score,
            'max_urls_per_domain': self.max_urls_per_domain,
            'request_timeout_seconds': self.request_timeout_seconds,
            'user_agent': self.user_agent,
            'source_weights': {
                'academic': self.source_weights.academic,
                'government': self.source_weights.government,
                'news': self.source_weights.news,
                'blog': self.source_weights.blog,
                'forum': self.source_weights.forum,
            },
            'local_scan_directories': self.local_scan_directories,
            'domain_blacklist': self.domain_blacklist,
            'domain_whitelist': self.domain_whitelist,
            'enable_wayback_check': self.enable_wayback_check,
            'enable_cross_referencing': self.enable_cross_referencing,
            'cache_validation_results': self.cache_validation_results,
            'cache_ttl_hours': self.cache_ttl_hours,
            'max_sources_per_type': self.max_sources_per_type,
            'credibility_threshold': self.credibility_threshold,
            'required_file_extensions': self.required_file_extensions,
            'language_filters': self.language_filters,
        }
        return result
    
    def validate(self) -> None:
        """Validate configuration parameters"""
        if not 0 <= self.min_credibility_score <= 1:
            raise ValueError("min_credibility_score must be between 0 and 1")
        
        if self.max_urls_per_domain < 1:
            raise ValueError("max_urls_per_domain must be at least 1")
        
        if self.request_timeout_seconds < 1:
            raise ValueError("request_timeout_seconds must be at least 1")
        
        if not 0 <= self.credibility_threshold <= 1:
            raise ValueError("credibility_threshold must be between 0 and 1")