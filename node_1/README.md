# Source Discovery Agent - Complete Implementation Guide

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Design Decisions](#design-decisions)
6. [Integration Guide](#integration-guide)
7. [Configuration](#configuration)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)
10. [Extension Points](#extension-points)

---

## Overview

The Source Discovery Agent is a production-ready, highly optimized component designed for multi-agent research automation pipelines. It autonomously discovers, validates, and scores information sources based on configurable credibility requirements.

### Key Features

✅ **LangGraph Integration**: Built as a native LangGraph node with typed state management  
✅ **Web Search**: Free, open-source search using googlesearch-python  
✅ **Robots.txt Compliance**: Full RFC compliance with caching  
✅ **Credibility Scoring**: Multi-factor domain authority and relevance scoring  
✅ **Rich Metadata**: Comprehensive source metadata extraction  
✅ **Error Handling**: Graceful degradation and comprehensive logging  
✅ **Rate Limiting**: Ethical scraping with configurable delays  
✅ **Production-Ready**: Thread-safe, cached, and optimized for scale  

---

## Architecture

### High-Level Flow

```
┌─────────────────────┐
│  Process           │
│  Orchestrator      │
│  (Upstream)        │
└─────────┬───────────┘
          │ SourceDiscoveryInput
          ▼
┌─────────────────────┐
│  SEARCH NODE        │
│  • Web Search       │
│  • URL Discovery    │
└─────────┬───────────┘
          │ raw_urls
          ▼
┌─────────────────────┐
│  VALIDATION NODE    │
│  • Robots.txt       │
│  • Fetch Metadata   │
│  • Score Sources    │
│  • Validate Rules   │
└─────────┬───────────┘
          │ validated_sources
          ▼
┌─────────────────────┐
│  OUTPUT NODE        │
│  • Format Results   │
│  • Sort by Score    │
└─────────┬───────────┘
          │ SourceDiscoveryOutput
          ▼
┌─────────────────────┐
│  Downstream Agents  │
│  • Web Scraper      │
│  • File Loader      │
└─────────────────────┘
```

### Component Architecture

```
Source Discovery Agent
├── Pydantic Models (Data Schemas)
│   ├── CredibilityRequirements
│   ├── SourceMetadata
│   ├── SourceDiscoveryInput
│   └── SourceDiscoveryOutput
│
├── Utility Classes (Core Logic)
│   ├── RobotsTxtChecker (robots.txt validation & caching)
│   ├── CredibilityScorer (domain authority heuristics)
│   ├── RelevanceScorer (keyword-based relevance)
│   └── PageFetcher (HTTP fetching & metadata extraction)
│
├── Agent Logic
│   └── SourceDiscoveryAgent (orchestrates utilities)
│
└── LangGraph Nodes
    ├── search_node (web search)
    ├── validation_node (validation & scoring)
    └── output_node (result formatting)
```

---

## Installation

### Prerequisites

- Python 3.9+
- pip package manager

### Required Dependencies

```bash
# Core framework dependencies
pip install langgraph langchain pydantic

# Web scraping and parsing
pip install beautifulsoup4 requests

# Free web search (unofficial Google search)
pip install googlesearch-python

# Optional: LangSmith for tracing (requires account)
# pip install langsmith
```

### Complete Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install langgraph langchain pydantic beautifulsoup4 requests googlesearch-python

# Verify installation
python -c "import langgraph, pydantic, bs4, googlesearch; print('All dependencies installed!')"
```

---

## Quick Start

### Basic Usage

```python
from source_discovery_agent import (
    SourceDiscoveryInput,
    CredibilityRequirements,
    run_source_discovery
)

# Define your research topic and requirements
input_data = SourceDiscoveryInput(
    topic="machine learning interpretability",
    max_results=10,
    credibility_requirements=CredibilityRequirements(
        min_domain_authority=0.7,
        max_age_days=365,
        require_https=True
    )
)

# Run the agent
output = run_source_discovery(input_data)

# Access results
for source in output.sources:
    print(f"{source.title}: {source.url}")
    print(f"  Authority: {source.domain_authority_score:.2f}")
    print(f"  Relevance: {source.relevance_score:.2f}")
```

### Running the Example

```bash
# Run the built-in example
python source_discovery_agent.py

# The example will:
# 1. Search for "AI ethics and bias mitigation"
# 2. Validate 15 sources
# 3. Display top 5 results with metadata
```

---

## Design Decisions

### 1. **LangGraph vs CrewAI**

**Decision**: Use LangGraph  
**Rationale**: 
- Better state management for stateful workflows
- Native support for checkpointing and human-in-the-loop
- More granular control over execution flow
- Better integration with LangSmith for production monitoring

### 2. **Web Search Strategy**

**Decision**: Use `googlesearch-python` library  
**Rationale**:
- Free and open-source (no API key required)
- Simple interface
- Adequate for research use cases

**Alternatives Considered**:
- SerpAPI: Excellent but limited free tier (100 searches/month)
- Google Custom Search API: Requires API key, usage limits
- Custom crawler: Too complex, would need seed URLs

**Limitation**: Rate limiting by Google - recommended to use 15s delays between searches in production.

### 3. **Credibility Scoring Approach**

**Decision**: Heuristic-based with extensible architecture  
**Rationale**:
- Free Moz DA API no longer available
- Commercial APIs (Ahrefs, SEMrush) are expensive
- Heuristic approach using TLDs, HTTPS, domain patterns is sufficient for research use

**Current Heuristics**:
- `.edu` domains: 0.85-0.9
- `.gov` domains: 0.9-0.95
- HTTPS: +0.05 bonus
- Research-related subdomains: +0.05
- Trusted domain whitelist: configurable scores

**Extension Point**: Replace `CredibilityScorer.compute_domain_authority()` with external API call.

### 4. **Relevance Scoring**

**Decision**: Keyword-based matching  
**Rationale**:
- Lightweight and fast
- No external dependencies (like ML models)
- Sufficient accuracy for filtering

**Alternatives Considered**:
- TF-IDF with sklearn: Too heavy for simple filtering
- Sentence embeddings: Requires model downloads and GPU
- Full NLP pipeline: Overkill for this use case

**Extension Point**: Replace `RelevanceScorer.compute_relevance()` with embedding-based similarity.

### 5. **Error Handling Philosophy**

**Decision**: Fail gracefully, never crash  
**Rationale**:
- Single source failure shouldn't stop entire workflow
- Partial results are better than no results
- Detailed logging enables debugging

**Implementation**:
- Try-except blocks around all network operations
- Default values when parsing fails
- Comprehensive error metadata in output

### 6. **Rate Limiting**

**Decision**: Conservative delays (2s between requests)  
**Rationale**:
- Ethical web scraping
- Avoid IP bans
- Respect server resources

**Configuration**:
```python
REQUEST_DELAY = 2.0  # seconds between requests
```

Adjust based on your use case, but never go below 1s.

---

## Integration Guide

### Integration with Process Orchestrator (Upstream)

The Process Orchestrator should pass input to this agent via the shared LangGraph state:

```python
from langgraph.graph import StateGraph
from source_discovery_agent import (
    create_source_discovery_graph,
    SourceDiscoveryInput,
    CredibilityRequirements
)

# In your main orchestrator graph
class OrchestratorState(TypedDict):
    research_topic: str
    discovered_sources: List[SourceMetadata]
    # ... other fields

def orchestrator_node(state: OrchestratorState) -> OrchestratorState:
    # Create input for Source Discovery Agent
    discovery_input = SourceDiscoveryInput(
        topic=state['research_topic'],
        max_results=20,
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.7
        )
    )
    
    # Run Source Discovery Agent
    discovery_output = run_source_discovery(discovery_input)
    
    # Update state with results
    state['discovered_sources'] = discovery_output.sources
    
    return state
```

### Integration with Web Scraper Engine (Downstream)

The Web Scraper Engine receives the validated source list:

```python
def web_scraper_node(state: OrchestratorState) -> OrchestratorState:
    sources = state['discovered_sources']
    
    # Filter sources that allow scraping
    scrapable_sources = [
        s for s in sources 
        if s.robots_allowed and s.validation_status
    ]
    
    # Prioritize by authority score
    sorted_sources = sorted(
        scrapable_sources,
        key=lambda s: s.domain_authority_score,
        reverse=True
    )
    
    # Scrape each source
    for source in sorted_sources:
        content = scrape_url(source.url)
        # Process content...
    
    return state
```

### Integration with Local File Loader (Downstream)

The File Loader can extract PDF sources:

```python
def file_loader_node(state: OrchestratorState) -> OrchestratorState:
    sources = state['discovered_sources']
    
    # Filter PDF sources
    pdf_sources = [
        s for s in sources 
        if s.content_type == 'pdf' and s.validation_status
    ]
    
    # Download and process PDFs
    for source in pdf_sources:
        pdf_content = download_pdf(source.url)
        # Extract text from PDF...
    
    return state
```

### Complete Multi-Agent Example

```python
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, List

class ResearchState(TypedDict):
    topic: str
    sources: List[SourceMetadata]
    scraped_content: List[Dict]
    pdf_content: List[Dict]

def create_research_pipeline():
    workflow = StateGraph(ResearchState)
    
    # Add nodes
    workflow.add_node("discover", source_discovery_node)
    workflow.add_node("scrape", web_scraper_node)
    workflow.add_node("load_pdfs", pdf_loader_node)
    workflow.add_node("analyze", analysis_node)
    
    # Define flow
    workflow.add_edge(START, "discover")
    workflow.add_edge("discover", "scrape")
    workflow.add_edge("discover", "load_pdfs")  # Parallel
    workflow.add_edge("scrape", "analyze")
    workflow.add_edge("load_pdfs", "analyze")
    workflow.add_edge("analyze", END)
    
    return workflow.compile()
```

---

## Configuration

### Environment Variables

For production deployment, use environment variables:

```python
import os

# In source_discovery_agent.py, update:
USER_AGENT = os.getenv('AGENT_USER_AGENT', 'ResearchBot/1.0')
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '10'))
REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '2.0'))
```

### Trusted Domains Configuration

Extend the trusted domains list:

```python
CUSTOM_TRUSTED_DOMAINS = {
    'nature.com': 0.95,
    'science.org': 0.95,
    'plos.org': 0.85,
    'bmj.com': 0.9,
    'thelancet.com': 0.9,
    # Add your domain-specific trusted sources
}

# Merge with defaults
TRUSTED_DOMAINS.update(CUSTOM_TRUSTED_DOMAINS)
```

### Credibility Requirements Profiles

Create reusable requirement profiles:

```python
# High-rigor academic research
ACADEMIC_REQUIREMENTS = CredibilityRequirements(
    min_domain_authority=0.8,
    max_age_days=365,
    trusted_domains=['edu', 'gov', 'arxiv.org'],
    require_https=True,
    min_relevance_score=0.6
)

# General web research
GENERAL_REQUIREMENTS = CredibilityRequirements(
    min_domain_authority=0.5,
    max_age_days=730,
    require_https=False,
    min_relevance_score=0.3
)

# News and current events
NEWS_REQUIREMENTS = CredibilityRequirements(
    min_domain_authority=0.6,
    max_age_days=30,  # Recent news only
    required_content_types=['news', 'article'],
    require_https=True,
    min_relevance_score=0.5
)
```

---

## Testing

### Unit Tests

```python
import unittest
from source_discovery_agent import (
    CredibilityScorer,
    RelevanceScorer,
    RobotsTxtChecker
)

class TestCredibilityScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = CredibilityScorer()
    
    def test_edu_domain(self):
        score = self.scorer.compute_domain_authority('https://mit.edu/research')
        self.assertGreater(score, 0.8)
    
    def test_https_bonus(self):
        score_https = self.scorer.compute_domain_authority('https://example.com')
        score_http = self.scorer.compute_domain_authority('http://example.com')
        self.assertGreater(score_https, score_http)

class TestRelevanceScorer(unittest.TestCase):
    def test_relevance_computation(self):
        score, keywords = RelevanceScorer.compute_relevance(
            topic="machine learning",
            title="Introduction to Machine Learning",
            description="A comprehensive guide to machine learning algorithms"
        )
        self.assertGreater(score, 0.5)
        self.assertIn('machine', keywords)

class TestRobotsTxtChecker(unittest.TestCase):
    def setUp(self):
        self.checker = RobotsTxtChecker()
    
    def test_allowed_url(self):
        can_fetch, delay = self.checker.can_fetch('https://www.python.org/')
        self.assertTrue(can_fetch)

if __name__ == '__main__':
    unittest.main()
```

### Integration Test

```python
def test_full_workflow():
    """Test complete workflow with a real topic"""
    input_data = SourceDiscoveryInput(
        topic="Python web scraping",
        max_results=5,
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.5
        )
    )
    
    output = run_source_discovery(input_data)
    
    # Assertions
    assert output.total_discovered > 0, "Should discover at least one source"
    assert output.total_validated >= 0, "Should have validation results"
    assert len(output.sources) == output.total_validated
    
    # Check source quality
    for source in output.sources:
        assert source.validation_status is True
        assert source.domain_authority_score >= 0.5
        assert source.url.startswith('http')
    
    print(f"✅ Integration test passed: {output.total_validated} sources validated")

if __name__ == '__main__':
    test_full_workflow()
```

---

## Troubleshooting

### Issue: No sources found

**Symptoms**: `total_discovered = 0`

**Causes**:
1. Rate limiting by Google
2. Network connectivity issues
3. Topic too specific

**Solutions**:
```python
# 1. Increase delay between searches
REQUEST_DELAY = 5.0  # Increase from 2.0

# 2. Try a broader topic
input_data.topic = "machine learning"  # Instead of "machine learning interpretability in healthcare"

# 3. Check network connectivity
import requests
try:
    requests.get('https://www.google.com', timeout=5)
    print("Network OK")
except:
    print("Network issue detected")
```

### Issue: All sources fail validation

**Symptoms**: `total_validated = 0` but `total_discovered > 0`

**Causes**:
1. Requirements too strict
2. Sources don't meet HTTPS requirement
3. Relevance threshold too high

**Solutions**:
```python
# Relax requirements
input_data.credibility_requirements = CredibilityRequirements(
    min_domain_authority=0.3,  # Lower from 0.7
    require_https=False,       # Allow HTTP
    min_relevance_score=0.2    # Lower threshold
)
```

### Issue: Slow execution

**Symptoms**: Takes > 60 seconds for 10 sources

**Causes**:
1. Large REQUEST_DELAY
2. Slow network
3. Many retries

**Solutions**:
```python
# Reduce delays (carefully!)
REQUEST_DELAY = 1.0  # Minimum recommended

# Reduce retries
MAX_RETRIES = 1  # From 3

# Reduce timeout
REQUEST_TIMEOUT = 5  # From 10
```

### Issue: robots.txt errors

**Symptoms**: Many "robots.txt fetch failed" warnings

**Causes**:
1. Target site doesn't have robots.txt (not an error)
2. Network timeout

**Solutions**:
- This is normal behavior - agent defaults to "allowed" when robots.txt is missing
- No action needed unless you want to be extra cautious:

```python
# Stricter robots.txt handling
def validate_source(self, url, topic, requirements):
    can_fetch, _ = self.robots_checker.can_fetch(url)
    if not can_fetch:
        # Fail immediately instead of defaulting to allowed
        raise ValueError("Robots.txt disallows access")
```

---

## Extension Points

### 1. Add External Domain Authority API

Replace the heuristic scorer with a real API:

```python
class CredibilityScorer:
    def compute_domain_authority(self, url: str) -> float:
        # Option 1: Moz API (requires paid account)
        # return self.fetch_moz_da(url)
        
        # Option 2: Ahrefs API
        # return self.fetch_ahrefs_dr(url)
        
        # Option 3: Custom ML model
        # return self.ml_model.predict(url)
        
        # Fallback to heuristic
        return self.heuristic_score(url)
```

### 2. Add Machine Learning Relevance Scoring

Use embeddings for better relevance:

```python
from sentence_transformers import SentenceTransformer

class MLRelevanceScorer:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def compute_relevance(self, topic: str, title: str, description: str) -> float:
        # Encode texts
        topic_embedding = self.model.encode(topic)
        content_embedding = self.model.encode(f"{title} {description}")
        
        # Compute cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarity = cosine_similarity(
            [topic_embedding],
            [content_embedding]
        )[0][0]
        
        return float(similarity)
```

### 3. Add Async/Parallel Processing

For better performance with many sources:

```python
import asyncio
import aiohttp

class AsyncPageFetcher:
    async def fetch_metadata_async(self, urls: List[str]) -> List[Dict]:
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_one(session, url) for url in urls]
            return await asyncio.gather(*tasks)
    
    async def fetch_one(self, session, url):
        async with session.get(url) as response:
            html = await response.text()
            # Parse with BeautifulSoup...
            return metadata

# In validation_node:
async def validation_node_async(state: AgentState) -> AgentState:
    fetcher = AsyncPageFetcher()
    metadata_list = await fetcher.fetch_metadata_async(state['raw_urls'])
    # Process in parallel...
```

### 4. Add LangSmith Tracing

For production monitoring:

```python
import os
os.environ['LANGSMITH_API_KEY'] = 'your-api-key'
os.environ['LANGSMITH_TRACING'] = 'true'
os.environ['LANGSMITH_PROJECT'] = 'source-discovery-agent'

# LangGraph automatically integrates with LangSmith
# All node executions will be traced
```

### 5. Add Caching Layer

Cache search results to avoid repeated queries:

```python
import json
from pathlib import Path

class SearchCache:
    def __init__(self, cache_dir: str = './cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cached_results(self, topic: str) -> Optional[List[str]]:
        cache_file = self.cache_dir / f"{hash(topic)}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                # Check if cache is still valid (e.g., < 24 hours old)
                if self.is_valid(data['timestamp']):
                    return data['urls']
        return None
    
    def cache_results(self, topic: str, urls: List[str]):
        cache_file = self.cache_dir / f"{hash(topic)}.json"
        with open(cache_file, 'w') as f:
            json.dump({
                'topic': topic,
                'urls': urls,
                'timestamp': datetime.utcnow().isoformat()
            }, f)
```

---

## Performance Optimization

### Benchmarks

On a typical workload (10 sources, moderate requirements):

| Phase | Time | Bottleneck |
|-------|------|------------|
| Search | 5-10s | Google rate limiting |
| Validation | 15-25s | HTTP requests (2s delay × 10) |
| Output | <1s | CPU (negligible) |
| **Total** | **20-35s** | Network I/O |

### Optimization Strategies

1. **Parallel Validation**: Process multiple sources concurrently
2. **Aggressive Caching**: Cache robots.txt, page metadata, search results
3. **Batch Processing**: Group requests to same domain
4. **CDN Integration**: Fetch from CDN when available
5. **Async I/O**: Use `aiohttp` instead of `requests`

---

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY source_discovery_agent.py .

# Run as non-root user
RUN useradd -m agent
USER agent

CMD ["python", "source_discovery_agent.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: source-discovery-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: source-discovery
  template:
    metadata:
      labels:
        app: source-discovery
    spec:
      containers:
      - name: agent
        image: source-discovery-agent:latest
        env:
        - name: REQUEST_DELAY
          value: "2.0"
        - name: LANGSMITH_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: langsmith-api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

---

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: [link]
- Email: research-automation@example.com
- Slack: #research-agents

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Maintainer**: AI Research Systems Team
