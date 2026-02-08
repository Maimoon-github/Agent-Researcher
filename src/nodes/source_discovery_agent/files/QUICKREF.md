# Source Discovery Agent - Quick Reference

## Installation

```bash
pip install -r requirements.txt --break-system-packages
pip install -e .
```

## Basic Usage

```python
from source_discovery_agent import SourceDiscoveryAgent

# Initialize
agent = SourceDiscoveryAgent()

# Discover sources
result = agent.discover_sources(query="your research query")

# Access results
if result["status"] == "success":
    urls = [s["url"] for s in result["data"]["validated_urls"]]
```

## Configuration

```python
from source_discovery_agent import SourceDiscoveryConfig

config = SourceDiscoveryConfig(
    min_credibility_score=0.8,
    max_urls_per_domain=5,
    local_scan_directories=["/path/to/docs"]
)

agent = SourceDiscoveryAgent(config=config)
```

## Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | Required | Research query string |
| `source_type_preferences` | List[str] | `["web", "academic"]` | Preferred source types |
| `credibility_threshold` | float | 0.7 | Minimum credibility score (0-1) |
| `max_sources_per_type` | int | 10 | Max sources per type |

## Response Structure

```python
{
    "status": "success",
    "query_id": "uuid",
    "processing_time_ms": 245,
    "data": {
        "search_terms": [...],
        "validated_urls": [...],
        "local_file_patterns": [...],
        "source_types_identified": [...],
        "discovery_metrics": {...},
        "recommendations": {...}
    }
}
```

## Common Operations

### Get Metrics
```python
metrics = agent.get_metrics()
print(f"Cache hit rate: {metrics['cache_hit_rate']:.2%}")
```

### Reset Metrics
```python
agent.reset_metrics()
```

### Custom Scoring
```python
from source_discovery_agent import CredibilityScorer

scorer = CredibilityScorer()
score = scorer.calculate_score("https://example.com")
breakdown = scorer.get_score_breakdown("https://example.com")
```

## Source Types

- `web` - General web sources
- `academic` - Academic journals, papers
- `news` - News organizations
- `technical` - Technical documentation
- `local` - Local file system

## Error Handling

```python
result = agent.discover_sources(query="test")

if result["status"] == "error":
    error = result["error"]
    print(f"Error: {error['message']}")
    print(f"Suggestions: {error['suggestions']}")
```

## Configuration File

```yaml
source_discovery:
  min_credibility_score: 0.7
  max_urls_per_domain: 5
  local_scan_directories:
    - "/path/to/documents"
  domain_blacklist:
    - "spam-site.com"
```

Load with:
```python
config = SourceDiscoveryConfig.from_yaml("config.yaml")
```

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=source_discovery_agent tests/

# Run specific test
pytest tests/test_agent.py::test_discover_sources
```

## CLI Usage (Future)

```bash
# Basic discovery
source-discovery "your research query"

# With options
source-discovery "query" --threshold 0.8 --max-sources 10

# Output to file
source-discovery "query" --output results.json
```

## Credibility Score Components

| Component | Weight | Range |
|-----------|--------|-------|
| Domain Authority | 30% | 0-30 |
| Content Quality | 40% | 0-40 |
| External Validation | 30% | 0-30 |

Total: 0.0 - 1.0 (normalized)

## Known High-Authority Domains

- `*.edu` - Educational institutions
- `*.gov` - Government sites
- `arxiv.org` - Preprint server
- `pubmed.ncbi.nlm.nih.gov` - Medical research
- `nature.com`, `science.org` - Scientific journals

## Performance Tips

1. Enable caching for repeated queries
2. Set appropriate timeouts
3. Use domain blacklists to filter spam
4. Adjust credibility threshold based on needs
5. Limit sources per domain to ensure diversity

## Troubleshooting

### No sources found
- Lower credibility threshold
- Expand search terms
- Check network connectivity

### Slow performance
- Reduce `max_sources_per_type`
- Enable caching
- Increase `request_timeout_seconds`

### Too many low-quality sources
- Raise credibility threshold
- Use domain whitelist
- Adjust source type weights

## Support

- GitHub: https://github.com/yourusername/source-discovery-agent
- Issues: https://github.com/yourusername/source-discovery-agent/issues
- Docs: https://source-discovery-agent.readthedocs.io
