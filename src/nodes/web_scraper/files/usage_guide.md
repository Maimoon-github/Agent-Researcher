# Web Scraper Engine - Usage Guide

This guide provides detailed instructions and examples for using the Web Scraper Engine effectively.

## Table of Contents

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
3. [Configuration](#configuration)
4. [Advanced Features](#advanced-features)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

## Installation

### Step 1: Install Dependencies

```bash
# Clone the repository
cd web_scraper_engine

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (for JavaScript-rendered sites)
playwright install chromium
```

### Step 2: Verify Installation

```python
from src.nodes.web_scraper import WebScraperEngine

scraper = WebScraperEngine()
print("Installation successful!")
```

## Basic Usage

### Example 1: Scrape a Single URL

```python
from src.nodes.web_scraper import WebScraperEngine

# Initialize engine
scraper = WebScraperEngine()

# Prepare URL
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

# Scrape
result = scraper.scrape_urls(url_batch=url_batch)

# Access results
if result['status'] == 'success':
    for item in result['data']['scraped_data']:
        print(f"Title: {item['extracted_content']['title']}")
        print(f"Text: {item['extracted_content']['text'][:500]}...")
```

### Example 2: Scrape Multiple URLs

```python
url_batch = [
    {
        "url": "https://example.com/article1",
        "domain": "example.com",
        "credibility_score": 0.9,
        "robots_allowed": True,
        "source_type": "news",
        "validation_timestamp": "2024-01-15T10:00:00Z",
        "metadata": {}
    },
    {
        "url": "https://example.com/article2",
        "domain": "example.com",
        "credibility_score": 0.9,
        "robots_allowed": True,
        "source_type": "news",
        "validation_timestamp": "2024-01-15T10:00:00Z",
        "metadata": {}
    }
]

result = scraper.scrape_urls(url_batch=url_batch)
print(f"Scraped {len(result['data']['scraped_data'])} URLs")
```

## Configuration

### Using YAML Configuration

1. Edit `config/scraper_config.yaml`:

```yaml
web_scraper:
  default_delay_seconds: 2.0
  max_concurrent_requests: 5
  enable_caching: true
  cache_ttl_hours: 48
```

2. Load and use:

```python
import yaml

with open('config/scraper_config.yaml', 'r') as f:
    config = yaml.safe_load(f)['web_scraper']

scraper = WebScraperEngine(config=config)
```

### Using Python Dictionary

```python
config = {
    'default_delay_seconds': 1.5,
    'max_concurrent_requests': 8,
    'enable_caching': True,
    'cache_ttl_hours': 24,
    'min_content_length_chars': 150,
    'preserve_structure': True,
    'discover_new_links': True,
    'same_domain_only': False
}

scraper = WebScraperEngine(config=config)
```

## Advanced Features

### 1. Custom Extraction Patterns

For sites with specific HTML structure:

```python
# Define patterns
extraction_patterns = {
    "main_content": "article.post-content",
    "title": "h1.post-title",
    "author": "span.author-name",
    "date_published": "time.published",
    "categories": "a.category-tag"
}

# Use patterns
result = scraper.scrape_urls(
    url_batch=url_batch,
    extraction_patterns=extraction_patterns
)
```

### 2. Domain-Specific Rules

Add permanent rules for specific domains in `src/nodes/web_scraper/config.py`:

```python
DOMAIN_RULES = {
    "myblog.com": {
        "extraction_patterns": {
            "main_content": ".post-body",
            "title": "h1.title",
            "author": ".author"
        },
        "rate_limit": 2.0,  # Wait 2 seconds between requests
        "requires_javascript": False
    }
}
```

### 3. Proxy Rotation

#### Step 1: Create proxy list

Create `config/proxies.txt`:

```
http://proxy1.example.com:8080
http://proxy2.example.com:8080
socks5://proxy3.example.com:1080
```

#### Step 2: Enable proxy rotation

```python
config = {
    'enable_proxy_rotation': True,
    'proxy_list_file': 'config/proxies.txt'
}

scraper = WebScraperEngine(config=config)
```

### 4. Caching Strategy

```python
# Enable caching with long TTL
config = {
    'enable_caching': True,
    'cache_ttl_hours': 72,  # 3 days
    'cache_storage_path': 'data/cache/my_scraper'
}

scraper = WebScraperEngine(config=config)

# First scrape - fetches from web
result1 = scraper.scrape_urls(url_batch)

# Second scrape - uses cache
result2 = scraper.scrape_urls(url_batch)

# Check cache stats
cache_stats = scraper.cache_middleware.get_stats()
print(f"Cache hit rate: {cache_stats['hit_rate']:.2%}")
```

### 5. Link Discovery

```python
config = {
    'discover_new_links': True,
    'same_domain_only': True,
    'max_follow_depth': 2
}

scraper = WebScraperEngine(config=config)
result = scraper.scrape_urls(url_batch)

# Get discovered links
for item in result['data']['scraped_data']:
    discovered_links = item.get('discovered_links', [])
    print(f"Found {len(discovered_links)} new links")
    
    for link in discovered_links[:5]:
        print(f"  - {link['url']}")
        print(f"    Anchor: {link['anchor_text']}")
        print(f"    Context: {link['discovery_context']}")
```

### 6. Content Validation

```python
# Set strict validation rules
config = {
    'min_content_length_chars': 500,
    'max_content_length_chars': 50000
}

scraper = WebScraperEngine(config=config)
result = scraper.scrape_urls(url_batch)

# Check validation results
for item in result['data']['scraped_data']:
    validation = item.get('validation', {})
    if validation['is_valid']:
        print(f"✓ Valid: {item['source_url']}")
    else:
        print(f"✗ Invalid: {item['source_url']}")
        print(f"  Errors: {validation['errors']}")
```

### 7. Metrics and Monitoring

```python
scraper = WebScraperEngine()

# Scrape some URLs
result = scraper.scrape_urls(url_batch)

# Get comprehensive metrics
metrics = scraper.get_metrics()

print("Overall Stats:")
print(f"  Total requests: {metrics['stats']['total_requests']}")
print(f"  Successful: {metrics['stats']['successful_scrapes']}")
print(f"  Failed: {metrics['stats']['failed_scrapes']}")
print(f"  Success rate: {metrics['stats']['successful_scrapes']/metrics['stats']['total_requests']:.2%}")

print("\nRate Limiter Stats:")
for domain, stats in metrics['rate_limiter'].get('domain_stats', {}).items():
    print(f"  {domain}:")
    print(f"    Current delay: {stats['current_delay']}s")
    print(f"    Avg response time: {stats['avg_response_time_ms']:.0f}ms")

print("\nCache Stats:")
if metrics['cache']:
    print(f"  Hit rate: {metrics['cache']['hit_rate']:.2%}")
    print(f"  Total hits: {metrics['cache']['hits']}")
    print(f"  Cache size: {metrics['cache']['cache_size']}")
```

## Best Practices

### 1. Start with Conservative Settings

```python
config = {
    'default_delay_seconds': 2.0,  # Start slow
    'max_concurrent_requests': 3,  # Low concurrency
    'enable_caching': True,
    'discover_new_links': False  # Don't follow links initially
}
```

### 2. Handle Errors Gracefully

```python
result = scraper.scrape_urls(url_batch)

if result['status'] == 'success':
    # Process all successful items
    process_data(result['data']['scraped_data'])
    
elif result['status'] == 'partial_success':
    # Handle both successful and failed
    successful = result['data']['scraped_data']
    failed = result.get('failed_scrapes', [])
    
    process_data(successful)
    retry_failed(failed)
    
else:  # failure
    # Log and alert
    logger.error(f"Batch failed: {result.get('error_message')}")
    alert_admins(result)
```

### 3. Respect Robots.txt

```python
from src.nodes.web_scraper.utils import RobotsParser

robots_parser = RobotsParser()

# Check before adding to batch
if robots_parser.can_fetch(url):
    url_batch.append({
        "url": url,
        "robots_allowed": True,
        # ... other fields
    })
```

### 4. Use Appropriate Rate Limiting

```python
# For high-traffic sites
config = {'default_delay_seconds': 0.5}

# For small sites
config = {'default_delay_seconds': 3.0}

# Dynamic adjustment
scraper = WebScraperEngine()
metrics = scraper.get_metrics()

if metrics['rate_limiter']['domain_stats']['example.com']['error_count'] > 5:
    scraper.rate_limiter.increase_delay('example.com', factor=2.0)
```

### 5. Batch Processing

```python
# Process URLs in batches
all_urls = [...]  # Large list of URLs

batch_size = 50
for i in range(0, len(all_urls), batch_size):
    batch = all_urls[i:i+batch_size]
    
    result = scraper.scrape_urls(
        url_batch=batch,
        batch_id=f"batch_{i//batch_size}"
    )
    
    # Save results
    save_results(result)
    
    # Add delay between batches
    time.sleep(10)
```

## Troubleshooting

### Problem: High Failure Rate

**Symptoms:**
- Many failed scrapes
- Low success rate

**Solutions:**

```python
# 1. Increase delays
scraper.rate_limiter.increase_delay('example.com', factor=2.0)

# 2. Enable proxy rotation
config = {'enable_proxy_rotation': True}

# 3. Check robots.txt compliance
robots_parser = RobotsParser()
if not robots_parser.can_fetch(url):
    print(f"Blocked by robots.txt: {url}")

# 4. Reduce concurrency
config = {'max_concurrent_requests': 2}
```

### Problem: Low Extraction Quality

**Symptoms:**
- Low extraction confidence scores
- Missing content
- Incorrect data

**Solutions:**

```python
# 1. Add domain-specific patterns
extraction_patterns = {
    "main_content": "#actual-content-div",
    "title": "h1.article-title"
}

# 2. Check parser used
for item in result['data']['scraped_data']:
    parser = item['scraping_metadata']['parser_used']
    confidence = item['scraping_metadata']['extraction_confidence']
    print(f"Parser: {parser}, Confidence: {confidence}")

# 3. Inspect raw HTML
if config.get('extract_raw_html'):
    raw_html = item['extracted_content'].get('raw_html')
    # Manually inspect structure
```

### Problem: Cache Not Working

**Symptoms:**
- All requests fetch from web
- No cache hits

**Solutions:**

```python
# 1. Verify cache is enabled
print(f"Cache enabled: {scraper.cache_middleware is not None}")

# 2. Check cache directory
cache_stats = scraper.cache_middleware.get_stats()
print(f"Cache directory: {cache_stats['cache_dir']}")

# 3. Verify cache TTL
config = {'cache_ttl_hours': 48}  # Increase TTL

# 4. Clear old cache
scraper.cache_middleware.clear()
```

### Problem: Memory Usage

**Symptoms:**
- High memory consumption
- Out of memory errors

**Solutions:**

```python
# 1. Disable raw HTML storage
config = {'extract_raw_html': False}

# 2. Process in smaller batches
batch_size = 25  # Reduce from 50

# 3. Clear cache periodically
if iteration % 100 == 0:
    scraper.cache_middleware.clear()

# 4. Limit content length
config = {'max_content_length_chars': 50000}
```

## Advanced Patterns

### Pattern 1: Recursive Crawling

```python
visited = set()
to_visit = [initial_url]
max_depth = 3

for depth in range(max_depth):
    if not to_visit:
        break
    
    batch = to_visit[:50]
    to_visit = to_visit[50:]
    
    result = scraper.scrape_urls(url_batch=batch)
    
    for item in result['data']['scraped_data']:
        visited.add(item['final_url'])
        
        # Add discovered links
        for link in item.get('discovered_links', []):
            if link['url'] not in visited:
                to_visit.append(link['url'])
```

### Pattern 2: Retry Logic

```python
max_retries = 3

for attempt in range(max_retries):
    result = scraper.scrape_urls(url_batch)
    
    if result['status'] == 'success':
        break
    
    if attempt < max_retries - 1:
        wait_time = 2 ** attempt  # Exponential backoff
        time.sleep(wait_time)
```

### Pattern 3: Distributed Scraping

```python
from multiprocessing import Pool

def scrape_batch(batch):
    scraper = WebScraperEngine()
    return scraper.scrape_urls(url_batch=batch)

# Split URLs into chunks
chunks = [all_urls[i:i+50] for i in range(0, len(all_urls), 50)]

# Process in parallel
with Pool(processes=4) as pool:
    results = pool.map(scrape_batch, chunks)
```

## Support

For additional help:
- Check the [README](README.md) for overview
- Review [test examples](tests/test_scraper.py)
- Run [example.py](example.py) for working examples
- Open an issue on GitHub for bugs or feature requests