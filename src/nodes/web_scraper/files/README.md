# Web Scraper Engine

**Node 2: Web Data Extraction Specialist**

A production-grade web scraping system designed to extract structured data from web sources while respecting legal and ethical boundaries. Part of a larger Data Collection Pipeline architecture.

## Features

### Multi-Strategy Content Extraction
- **Newspaper3k**: Article-focused extraction with NLP enhancements
- **Readability**: Mozilla's algorithm for main content identification
- **Custom Selectors**: CSS/XPath patterns for domain-specific extraction
- **PDF Support**: Extract text from PDF documents
- **Fallback Heuristics**: Intelligent content detection when other methods fail

### Intelligent Rate Limiting
- Adaptive delays based on server response times and error rates
- Domain-specific rate limit configuration
- Robots.txt compliance with automatic parsing and caching
- Configurable concurrent requests per domain

### Content Processing & Enhancement
- Automatic language detection
- Readability scoring (Flesch Reading Ease)
- Spam/quality detection
- Sentiment analysis
- Named entity recognition
- Metadata extraction (author, date, keywords)

### Robust Error Handling
- Exponential backoff retry logic
- Proxy rotation with health checking
- Cache middleware for avoiding re-scraping
- Comprehensive error recovery strategies

### Link Discovery
- Intelligent link extraction with context awareness
- Pagination detection
- Link categorization (internal, external, media, documents)
- Relevance scoring for discovered links

## Architecture

```
src/nodes/web_scraper/
├── engine.py                    # Main orchestrator
├── config.py                    # Domain-specific rules
├── spiders/                     # Specialized spiders
├── middlewares/
│   ├── rate_limit_middleware.py
│   ├── proxy_rotation_middleware.py
│   ├── user_agent_middleware.py
│   └── cache_middleware.py
├── pipelines/
│   ├── content_pipeline.py      # Content processing
│   └── validation_pipeline.py   # Quality validation
├── extractors/
│   ├── newspaper_extractor.py
│   ├── readability_extractor.py
│   ├── custom_extractor.py
│   └── pdf_extractor.py
└── utils/
    ├── robots_parser.py
    ├── url_normalizer.py
    ├── content_cleaner.py
    └── link_analyzer.py
```

## Installation

### Requirements
- Python 3.8+
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install Playwright (for JavaScript-rendered sites)

```bash
playwright install
```

## Quick Start

### Basic Usage

```python
from src.nodes.web_scraper import WebScraperEngine

# Initialize engine
scraper = WebScraperEngine()

# Prepare URL batch
url_batch = [
    {
        "url": "https://example.com/article",
        "domain": "example.com",
        "credibility_score": 0.9,
        "robots_allowed": True,
        "source_type": "news",
        "validation_timestamp": "2024-01-15T10:00:00Z",
        "metadata": {}
    }
]

# Scrape URLs
result = scraper.scrape_urls(
    url_batch=url_batch,
    batch_id="batch_001",
    priority_level=1
)

# Process results
if result['status'] == 'success':
    for item in result['data']['scraped_data']:
        print(f"Title: {item['extracted_content']['title']}")
        print(f"Text: {item['extracted_content']['text'][:200]}...")
```

### With Custom Configuration

```python
config = {
    'default_delay_seconds': 2.0,
    'max_concurrent_requests': 5,
    'enable_caching': True,
    'cache_ttl_hours': 48,
    'min_content_length_chars': 200,
    'discover_new_links': True,
    'same_domain_only': True
}

scraper = WebScraperEngine(config=config)
```

### With Custom Extraction Patterns

```python
extraction_patterns = {
    "main_content": ".article-body",
    "title": "h1.article-title",
    "author": ".author-name",
    "date_published": "time.published",
    "categories": ".category-tag"
}

result = scraper.scrape_urls(
    url_batch=url_batch,
    extraction_patterns=extraction_patterns
)
```

## Configuration

### YAML Configuration (config/scraper_config.yaml)

```yaml
web_scraper:
  # Rate limiting
  default_delay_seconds: 1.0
  max_concurrent_requests: 10
  
  # Content extraction
  extract_raw_html: false
  min_content_length_chars: 100
  max_content_length_chars: 100000
  preserve_structure: true
  
  # Caching
  enable_caching: true
  cache_ttl_hours: 24
  cache_storage_path: "data/cache/web_scraper"
  
  # Error handling
  max_retries: 3
  retry_delay_seconds: 5
```

### Domain-Specific Rules

Add custom rules for specific domains in `src/nodes/web_scraper/config.py`:

```python
DOMAIN_RULES = {
    "example.com": {
        "extraction_patterns": {
            "main_content": ".main",
            "title": "h1",
            "author": ".author"
        },
        "rate_limit": 1.5,  # seconds between requests
        "requires_javascript": False
    }
}
```

## Input Contract

```json
{
  "required": {
    "url_batch": [
      {
        "url": "string (fully qualified URL)",
        "domain": "string",
        "credibility_score": "float (0.0-1.0)",
        "robots_allowed": "boolean",
        "source_type": "web|academic|news|government",
        "validation_timestamp": "ISO 8601 datetime",
        "metadata": {}
      }
    ],
    "batch_id": "UUID string",
    "priority_level": "integer (1=high, 5=low)"
  }
}
```

## Output Contract

```json
{
  "status": "success|partial_success|failure",
  "batch_id": "string",
  "processing_time_ms": "integer",
  "data": {
    "scraped_data": [
      {
        "source_url": "string",
        "final_url": "string",
        "http_status": "integer",
        "content_type": "string",
        "download_timestamp": "ISO 8601",
        "extracted_content": {
          "title": "string",
          "text": "string",
          "metadata": {
            "language_detected": "string",
            "readability_score": "float",
            "sentiment": "string"
          }
        }
      }
    ],
    "batch_statistics": {},
    "rate_limiting_report": {}
  }
}
```

## Advanced Features

### Proxy Rotation

```python
# Create proxy list file: config/proxies.txt
# http://proxy1:8080
# socks5://proxy2:1080

config = {
    'enable_proxy_rotation': True,
    'proxy_list_file': 'config/proxies.txt'
}

scraper = WebScraperEngine(config=config)
```

### Monitoring & Metrics

```python
# Get engine metrics
metrics = scraper.get_metrics()

print(f"Total requests: {metrics['stats']['total_requests']}")
print(f"Success rate: {metrics['stats']['successful_scrapes'] / metrics['stats']['total_requests']}")
print(f"Cache hit rate: {metrics['cache']['hit_rate']}")
```

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## Best Practices

### 1. Respect Robots.txt
The engine automatically checks and respects robots.txt rules. Ensure `robots_allowed` is set correctly in your URL batch.

### 2. Use Appropriate Rate Limiting
Start with conservative delays (1-2 seconds) and adjust based on the target domain's response.

### 3. Enable Caching
For repeated scraping of the same URLs, enable caching to reduce server load and improve performance.

### 4. Validate Before Processing
Always validate extracted content before downstream processing:

```python
if item['validation']['is_valid']:
    process_content(item['extracted_content'])
```

### 5. Handle Failures Gracefully
Check the status and handle partial successes:

```python
if result['status'] == 'partial_success':
    successful = result['data']['scraped_data']
    failed = result.get('failed_scrapes', [])
    # Handle both cases
```

## Error Handling

### Common Scenarios

**Network Timeout:**
- Automatic retry with exponential backoff
- Fallback to cached version if available
- Marked as failed after max retries

**IP Blocking/CAPTCHA:**
- Proxy rotation (if enabled)
- User agent rotation
- Increased delays for domain

**Content Parsing Failure:**
- Tries alternative extraction strategies
- Returns minimal metadata with error flag

## Performance Optimization

### 1. Batch Processing
Process URLs in batches of 10-50 for optimal performance.

### 2. Concurrent Requests
Adjust `max_concurrent_requests` based on your server capacity and target domains.

### 3. Caching Strategy
Enable caching for frequently accessed domains or repeated scraping tasks.

### 4. Selective Content Extraction
Set `extract_raw_html: false` to save storage space when only text is needed.

## Legal & Ethical Considerations

⚠️ **Important**: Always ensure your scraping activities comply with:

1. **Robots.txt**: Respect crawl delays and disallowed paths
2. **Terms of Service**: Check the website's ToS before scraping
3. **Copyright**: Don't scrape copyrighted content without permission
4. **Rate Limiting**: Don't overload servers with excessive requests
5. **Personal Data**: Comply with GDPR, CCPA, and other privacy regulations

## Troubleshooting

### High Failure Rate
- Check rate limiting settings
- Verify robots.txt compliance
- Enable proxy rotation
- Increase delays between requests

### Low Extraction Confidence
- Add domain-specific extraction patterns
- Check if site requires JavaScript rendering
- Verify content structure hasn't changed

### Cache Not Working
- Check cache directory permissions
- Verify cache_storage_path exists
- Check available disk space

## Contributing

Contributions are welcome! Please ensure:
1. Code follows PEP 8 style guidelines
2. All tests pass
3. New features include tests
4. Documentation is updated

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [Your Repo URL]
- Documentation: [Your Docs URL]
- Email: [Your Email]

## Changelog

### v1.0.0 (2024-01-15)
- Initial release
- Multi-strategy content extraction
- Adaptive rate limiting
- Comprehensive error handling
- Link discovery and categorization
