# Web Scraper Engine - Project Structure

## Complete Directory Tree

```
web_scraper_engine/
├── README.md                           # Main documentation
├── QUICKSTART.md                       # Quick start guide
├── USAGE_GUIDE.md                      # Comprehensive usage guide
├── requirements.txt                    # Python dependencies
├── setup.py                           # Package installation config
├── .gitignore                         # Git ignore rules
├── example.py                         # Example usage scripts
│
├── config/                            # Configuration files
│   ├── scraper_config.yaml           # Main YAML configuration
│   └── proxies.txt                   # Proxy list (optional, user-created)
│
├── src/                               # Source code
│   ├── __init__.py
│   └── nodes/
│       ├── __init__.py
│       └── web_scraper/              # Main package
│           ├── __init__.py           # Package exports
│           ├── engine.py             # Main orchestrator ⭐
│           ├── config.py             # Domain-specific rules
│           │
│           ├── extractors/           # Content extraction modules
│           │   ├── __init__.py
│           │   ├── newspaper_extractor.py    # Newspaper3k-based
│           │   ├── readability_extractor.py  # Readability-based
│           │   ├── custom_extractor.py       # Custom selectors
│           │   └── pdf_extractor.py          # PDF extraction
│           │
│           ├── middlewares/          # Request/response middlewares
│           │   ├── __init__.py
│           │   ├── rate_limit_middleware.py      # Adaptive rate limiting
│           │   ├── user_agent_middleware.py      # UA rotation
│           │   ├── proxy_rotation_middleware.py  # Proxy management
│           │   └── cache_middleware.py           # Caching layer
│           │
│           ├── pipelines/            # Content processing pipelines
│           │   ├── __init__.py
│           │   ├── content_pipeline.py       # Enhancement pipeline
│           │   └── validation_pipeline.py    # Quality validation
│           │
│           └── utils/                # Utility modules
│               ├── __init__.py
│               ├── robots_parser.py         # Robots.txt handling
│               ├── url_normalizer.py        # URL normalization
│               ├── content_cleaner.py       # Content cleaning
│               └── link_analyzer.py         # Link extraction
│
├── tests/                             # Test suite
│   ├── __init__.py
│   └── test_scraper.py               # Unit tests
│
└── data/                              # Data storage (auto-created)
    ├── cache/                        # Cached responses
    │   └── web_scraper/
    └── logs/                         # Log files
        └── scraper.log
```

## Key Files Explained

### Core Engine

**`src/nodes/web_scraper/engine.py`** (Main Orchestrator)
- Coordinates all scraping operations
- Implements 4-phase scraping process:
  1. Preparation & Resource Allocation
  2. Intelligent Scraping Execution
  3. Content Processing & Enhancement
  4. Link Discovery & Expansion
- ~400 lines of core logic

### Extractors (Content Extraction)

**`newspaper_extractor.py`**
- Uses newspaper3k library
- Best for news articles and blogs
- Includes NLP features (keywords, summary)

**`readability_extractor.py`**
- Uses Mozilla's Readability algorithm
- Good general-purpose extractor
- Preserves document structure

**`custom_extractor.py`**
- CSS/XPath selector support
- Fallback heuristic extraction
- Domain-specific pattern matching

**`pdf_extractor.py`**
- Extracts text from PDF files
- Handles metadata extraction
- Page-by-page processing

### Middlewares (Request/Response Processing)

**`rate_limit_middleware.py`**
- Adaptive rate limiting
- Domain-specific delays
- Error-based adjustment
- Performance monitoring

**`user_agent_middleware.py`**
- User agent rotation
- Configurable UA pool
- Random selection

**`proxy_rotation_middleware.py`**
- Proxy health checking
- Failure detection
- Automatic blacklisting
- Usage balancing

**`cache_middleware.py`**
- Disk-based caching
- TTL management
- Hit/miss tracking
- Automatic expiration

### Pipelines (Content Processing)

**`content_pipeline.py`**
- Language detection
- Readability scoring
- Sentiment analysis
- Spam detection
- Quality assessment

**`validation_pipeline.py`**
- Content length validation
- Language filtering
- Quality thresholds
- Error reporting

### Utils (Helper Modules)

**`robots_parser.py`**
- Parses robots.txt files
- Checks crawl permissions
- Extracts crawl delays
- Caches robot rules

**`url_normalizer.py`**
- URL normalization
- Tracking parameter removal
- Domain extraction
- URL validation

**`content_cleaner.py`**
- HTML cleaning
- Text normalization
- Boilerplate removal
- Encoding fixes

**`link_analyzer.py`**
- Link extraction
- Link categorization
- Pagination detection
- Relevance scoring

## Data Flow

```
Input (URL Batch)
    ↓
[Preparation Phase]
    • URL normalization
    • Robots.txt check
    • Domain grouping
    • Pattern selection
    ↓
[Scraping Phase]
    • Cache check
    • Rate limiting
    • HTTP request
    • Content download
    ↓
[Extraction Phase]
    • Multi-strategy extraction
    • Structure parsing
    • Metadata extraction
    ↓
[Processing Phase]
    • Content cleaning
    • Language detection
    • Quality scoring
    • Validation
    ↓
[Link Discovery Phase]
    • Link extraction
    • Link categorization
    • Relevance scoring
    ↓
Output (Structured Data)
```

## Configuration Layers

### 1. Default Configuration
Built into `engine.py` - used if no config provided

### 2. YAML Configuration
`config/scraper_config.yaml` - system-wide settings

### 3. Domain Rules
`src/nodes/web_scraper/config.py` - domain-specific patterns

### 4. Runtime Configuration
Passed to `WebScraperEngine()` - highest priority

### 5. Request-Level Overrides
Passed to `scrape_urls()` - per-request customization

## Extension Points

### Adding New Extractors

1. Create file in `extractors/`
2. Implement `extract(html, url)` method
3. Return dict with `extraction_confidence`
4. Add to strategy list in `engine.py`

Example:
```python
# src/nodes/web_scraper/extractors/my_extractor.py

class MyCustomExtractor:
    def extract(self, html, url):
        # Your extraction logic
        return {
            'title': extracted_title,
            'text': extracted_text,
            'extraction_confidence': 0.8
        }
```

### Adding New Middlewares

1. Create file in `middlewares/`
2. Implement required methods
3. Initialize in `engine.py`
4. Call in request/response cycle

### Adding New Pipelines

1. Create file in `pipelines/`
2. Implement `process(content)` method
3. Add to processing chain in `engine.py`

## Testing Structure

```
tests/
├── __init__.py
├── test_scraper.py           # Main tests
├── test_extractors.py        # Extractor tests (to be added)
├── test_middlewares.py       # Middleware tests (to be added)
└── test_utils.py             # Utility tests (to be added)
```

## Dependencies

### Core Dependencies
- **requests**: HTTP client
- **beautifulsoup4**: HTML parsing
- **lxml**: XML/HTML parser
- **newspaper3k**: Article extraction
- **readability-lxml**: Content extraction
- **pypdf**: PDF extraction

### Enhancement Dependencies
- **langdetect**: Language detection
- **textstat**: Readability scoring
- **vaderSentiment**: Sentiment analysis
- **ftfy**: Text fixing

### Infrastructure Dependencies
- **diskcache**: Caching
- **pyyaml**: Configuration
- **validators**: URL validation
- **playwright**: JavaScript rendering (optional)

## Performance Characteristics

### Memory Usage
- Base: ~50MB
- Per URL: ~1-5MB (without raw HTML)
- Per URL: ~5-20MB (with raw HTML)
- Cache: Variable (disk-based)

### Speed
- Simple page: 1-3 seconds
- With JS rendering: 5-10 seconds
- With rate limiting: +delay time
- From cache: <100ms

### Scalability
- Recommended batch size: 10-50 URLs
- Max concurrent: 10-20 requests
- Cache: Unlimited (disk space)
- Tested up to: 10,000 URLs/session

## Monitoring Points

### Metrics Collected
- Total requests
- Success/failure counts
- Response times
- Cache hit rates
- Domain-specific stats
- Proxy health
- Extraction confidence

### Access Metrics
```python
metrics = scraper.get_metrics()
```

## License & Attribution

This implementation follows the specification from the Web Scraper Engine architecture document, implementing:
- Multi-strategy content extraction
- Adaptive rate limiting
- Comprehensive error handling
- Professional-grade architecture

Built with Python 3.8+ and modern web scraping best practices.