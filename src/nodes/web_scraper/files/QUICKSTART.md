# Quick Start Guide - Web Scraper Engine

Get started with the Web Scraper Engine in 5 minutes!

## Installation

```bash
# 1. Navigate to project directory
cd web_scraper_engine

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Install Playwright for JavaScript-rendered sites
playwright install chromium
```

## Your First Scrape

Create a file `my_first_scrape.py`:

```python
from src.nodes.web_scraper import WebScraperEngine

# Initialize the engine
scraper = WebScraperEngine()

# Define URLs to scrape
url_batch = [
    {
        "url": "https://en.wikipedia.org/wiki/Web_scraping",
        "domain": "en.wikipedia.org",
        "credibility_score": 0.95,
        "robots_allowed": True,
        "source_type": "web",
        "validation_timestamp": "2024-01-15T10:00:00Z",
        "metadata": {}
    }
]

# Scrape!
result = scraper.scrape_urls(url_batch=url_batch)

# Show results
if result['status'] == 'success':
    for item in result['data']['scraped_data']:
        print(f"\n{'='*80}")
        print(f"Title: {item['extracted_content']['title']}")
        print(f"Language: {item['extracted_content']['metadata']['language_detected']}")
        print(f"Word count: {item['extracted_content'].get('word_count', 0)}")
        print(f"\nFirst 300 characters:")
        print(item['extracted_content']['text'][:300] + "...")
```

Run it:

```bash
python my_first_scrape.py
```

## Next Steps

### 1. Try the Examples

```bash
python example.py
```

### 2. Customize Configuration

```python
config = {
    'default_delay_seconds': 2.0,
    'enable_caching': True,
    'min_content_length_chars': 200
}

scraper = WebScraperEngine(config=config)
```

### 3. Add Custom Extraction Patterns

```python
patterns = {
    "main_content": ".article-body",
    "title": "h1.title",
    "author": ".author-name"
}

result = scraper.scrape_urls(
    url_batch=urls,
    extraction_patterns=patterns
)
```

### 4. Monitor Performance

```python
metrics = scraper.get_metrics()
print(f"Success rate: {metrics['stats']['successful_scrapes']/metrics['stats']['total_requests']:.2%}")
```

## Common Tasks

### Scrape Multiple Pages

```python
urls = [
    {"url": "https://example.com/page1", ...},
    {"url": "https://example.com/page2", ...},
    {"url": "https://example.com/page3", ...},
]

result = scraper.scrape_urls(url_batch=urls)
print(f"Scraped {len(result['data']['scraped_data'])} pages")
```

### Enable Caching

```python
config = {'enable_caching': True, 'cache_ttl_hours': 24}
scraper = WebScraperEngine(config=config)

# First scrape - fetches from web
result1 = scraper.scrape_urls(urls)

# Second scrape - uses cache (instant!)
result2 = scraper.scrape_urls(urls)
```

### Discover New Links

```python
config = {'discover_new_links': True, 'same_domain_only': True}
scraper = WebScraperEngine(config=config)

result = scraper.scrape_urls(urls)

for item in result['data']['scraped_data']:
    discovered = item.get('discovered_links', [])
    print(f"Found {len(discovered)} new links")
```

## Need Help?

- 📖 Read the [Full README](README.md)
- 📚 Check the [Usage Guide](USAGE_GUIDE.md)
- 🧪 Run tests: `pytest tests/`
- 💻 See [example.py](example.py) for more examples

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│         Web Scraper Engine                  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Newspaper│  │Readability│  │  Custom  │ │
│  │Extractor │  │ Extractor │  │Extractor │ │
│  └──────────┘  └──────────┘  └──────────┘ │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │      Content Pipeline                │  │
│  │  • Language Detection                │  │
│  │  • Readability Scoring               │  │
│  │  • Sentiment Analysis                │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │      Rate Limiter                    │  │
│  │  • Adaptive Delays                   │  │
│  │  • Domain-Specific Rules             │  │
│  └──────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

## What Makes This Engine Special?

✅ **Multi-Strategy Extraction** - Tries multiple methods to get the best content  
✅ **Adaptive Rate Limiting** - Automatically adjusts to server conditions  
✅ **Intelligent Caching** - Avoid re-scraping with smart cache  
✅ **Link Discovery** - Find related content automatically  
✅ **Content Quality Scoring** - Know how good your extraction is  
✅ **Robots.txt Compliance** - Respect website rules  
✅ **Comprehensive Metrics** - Monitor everything  

## Ready to Scale?

Check out the [Usage Guide](USAGE_GUIDE.md) for:
- Proxy rotation
- Distributed scraping
- Recursive crawling
- Error handling strategies
- Performance optimization

Happy Scraping! 🚀
