# Source Discovery Agent

A comprehensive Python agent for identifying, validating, and curating information sources for autonomous research workflows.

## Overview

The Source Discovery Agent is a research discovery and validation specialist designed to transform research queries into validated, credible source collections with comprehensive metadata scoring. It operates as the first child node in a research orchestration graph, providing downstream nodes with high-quality, validated sources.

## Features

- **Multi-Phase Discovery Process**
  - Phase 1: Query Analysis & Intent Understanding
  - Phase 2: Source Generation & Discovery
  - Phase 3: Validation & Credibility Assessment
  - Phase 4: Source Curation & Ranking

- **Comprehensive Validation**
  - URL syntax validation (RFC 3986 compliance)
  - Network reachability checks
  - robots.txt compliance
  - Multi-factor credibility scoring

- **Source Diversity**
  - Web sources (general, academic, news, technical)
  - Local file discovery
  - Multiple source type support

- **Credibility Scoring**
  - Domain authority assessment
  - Content quality evaluation
  - External validation metrics
  - Configurable thresholds

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd source-discovery-agent

# Install dependencies
pip install -r requirements.txt --break-system-packages

# Install the package
pip install -e .
```

## Quick Start

```python
from source_discovery_agent import SourceDiscoveryAgent

# Initialize the agent
agent = SourceDiscoveryAgent()

# Discover sources for a query
result = agent.discover_sources(
    query="Impact of climate change on biodiversity",
    source_type_preferences=["academic", "government"],
    max_sources_per_type=5
)

# Check if successful
if result["status"] == "success":
    # Get validated URLs
    urls = [source["url"] for source in result["data"]["validated_urls"]]
    print(f"Found {len(urls)} validated sources")
    
    # Get metrics
    metrics = result["data"]["discovery_metrics"]
    print(f"Credibility scores: {metrics['credibility_score_distribution']}")
else:
    print(f"Error: {result['error']['message']}")
```

## Configuration

### Using Default Configuration

```python
from source_discovery_agent import SourceDiscoveryAgent

agent = SourceDiscoveryAgent()
```

### Using Custom Configuration

```python
from source_discovery_agent import SourceDiscoveryAgent, SourceDiscoveryConfig

config = SourceDiscoveryConfig(
    min_credibility_score=0.8,
    max_urls_per_domain=3,
    request_timeout_seconds=15,
    local_scan_directories=["/data/research", "/home/user/documents"],
    enable_wayback_check=True
)

agent = SourceDiscoveryAgent(config=config)
```

### Loading Configuration from YAML

```python
from source_discovery_agent import SourceDiscoveryConfig, SourceDiscoveryAgent

config = SourceDiscoveryConfig.from_yaml("config.yaml")
agent = SourceDiscoveryAgent(config=config)
```

Example `config.yaml`:

```yaml
source_discovery:
  min_credibility_score: 0.7
  max_urls_per_domain: 5
  request_timeout_seconds: 10
  user_agent: "ResearchAgent/1.0 (Compatible; ResearchBot)"
  
  source_weights:
    academic: 1.2
    government: 1.3
    news: 1.0
    blog: 0.7
    forum: 0.5
    
  local_scan_directories:
    - "/data/research/sources"
    - "/home/user/documents"
    
  domain_blacklist:
    - "spam-site.com"
    
  enable_wayback_check: true
  enable_cross_referencing: true
  cache_validation_results: true
  cache_ttl_hours: 24
```

## API Reference

### SourceDiscoveryAgent.discover_sources()

Main entry point for source discovery.

**Parameters:**
- `query` (str): The research query string
- `query_id` (str, optional): UUID for tracking
- `source_type_preferences` (List[str], optional): Preferred source types
- `credibility_threshold` (float, optional): Minimum credibility score
- `max_sources_per_type` (int, optional): Maximum sources per type

**Returns:**
- Dictionary with discovered sources and metadata

**Example:**

```python
result = agent.discover_sources(
    query="Machine learning applications in healthcare",
    query_id="ml_health_001",
    source_type_preferences=["academic", "technical"],
    credibility_threshold=0.75,
    max_sources_per_type=10
)
```

### Response Format

#### Success Response

```json
{
  "status": "success",
  "query_id": "uuid-string",
  "processing_time_ms": 245,
  "data": {
    "search_terms": ["machine", "learning", "healthcare"],
    "validated_urls": [
      {
        "url": "https://example.com/article",
        "domain": "example.com",
        "credibility_score": 0.85,
        "robots_allowed": true,
        "source_type": "academic",
        "validation_timestamp": "2024-01-15T10:30:45Z",
        "metadata": {
          "title_extracted": "Article Title",
          "content_type": "text/html",
          "estimated_size_kb": 150
        }
      }
    ],
    "local_file_patterns": [],
    "source_types_identified": ["academic", "technical"],
    "discovery_metrics": {
      "total_sources_considered": 45,
      "validated_sources_count": 12,
      "validation_failures": 33,
      "processing_time_ms": 245,
      "credibility_score_distribution": {
        "min": 0.70,
        "max": 0.95,
        "average": 0.82,
        "median": 0.84
      }
    },
    "recommendations": {
      "primary_source_clusters": ["example.com", "research.org"],
      "suggested_next_queries": [],
      "coverage_gaps": ["recent case studies"],
      "confidence_level": 0.88
    }
  },
  "warnings": []
}
```

#### Error Response

```json
{
  "status": "error",
  "query_id": "uuid-string",
  "error": {
    "type": "no_sources_found",
    "code": "NO_SOURCES_FOUND",
    "message": "No sources met validation criteria",
    "details": {},
    "suggestions": [
      "Lower credibility threshold",
      "Try broader search terms"
    ],
    "fallback_actions": [
      "Returning empty result set"
    ]
  },
  "timestamp": "2024-01-15T10:30:45Z"
}
```

## Components

### QueryAnalyzer

Analyzes and normalizes research queries, extracting intent and requirements.

```python
from source_discovery_agent import QueryAnalyzer

analyzer = QueryAnalyzer()
analysis = analyzer.analyze("Impact of AI on employment")
```

### SourceGenerator

Generates potential sources based on query analysis.

```python
from source_discovery_agent import SourceGenerator

generator = SourceGenerator()
sources = generator.generate_sources(query_analysis, ["web", "academic"])
```

### SourceValidator

Validates sources for technical accessibility and compliance.

```python
from source_discovery_agent import SourceValidator

validator = SourceValidator()
result = validator.validate_source("https://example.com")
```

### CredibilityScorer

Multi-factor credibility assessment system.

```python
from source_discovery_agent import CredibilityScorer

scorer = CredibilityScorer()
score = scorer.calculate_score("https://example.com")
breakdown = scorer.get_score_breakdown("https://example.com")
```

### RobotsParser

Handles robots.txt compliance checking.

```python
from source_discovery_agent import RobotsParser

parser = RobotsParser()
is_allowed = parser.is_allowed("https://example.com/page")
delay = parser.get_crawl_delay("https://example.com")
```

### LocalFileDiscoverer

Discovers local files matching search criteria.

```python
from source_discovery_agent import LocalFileDiscoverer

discoverer = LocalFileDiscoverer(
    base_directories=["/data/research"],
    supported_extensions=["pdf", "md", "txt"]
)
files = discoverer.discover_files(query_analysis)
```

### SourceCurator

Curates and ranks sources for optimal research coverage.

```python
from source_discovery_agent import SourceCurator

curator = SourceCurator()
curated = curator.curate_sources(validated_sources, query_analysis)
```

## Metrics

Get comprehensive metrics about the discovery process:

```python
# Get current metrics
metrics = agent.get_metrics()

print(f"Total queries: {metrics['query_count']}")
print(f"Cache hit rate: {metrics['cache_hit_rate']:.2%}")
print(f"Validation success rate: {metrics['validation_success_rate']:.2%}")

# Reset metrics
agent.reset_metrics()
```

## Error Handling

The agent provides detailed error information with recovery suggestions:

```python
result = agent.discover_sources(query="test query")

if result["status"] == "error":
    error = result["error"]
    print(f"Error type: {error['type']}")
    print(f"Message: {error['message']}")
    print(f"Suggestions: {', '.join(error['suggestions'])}")
```

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=source_discovery_agent tests/

# Run specific test
pytest tests/test_agent.py::test_discover_sources
```

## Architecture

```
source_discovery_agent/
├── __init__.py              # Package initialization
├── agent.py                 # Main orchestration
├── query_analyzer.py        # Phase 1: Query analysis
├── source_generator.py      # Phase 2: Source generation
├── validator.py             # Phase 3: Validation
├── credibility_scorer.py    # Credibility scoring
├── robots_parser.py         # robots.txt handling
├── local_discoverer.py      # Local file discovery
├── curator.py               # Phase 4: Curation & ranking
├── config.py                # Configuration management
├── metrics.py               # Monitoring and metrics
└── exceptions.py            # Custom exceptions
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.
