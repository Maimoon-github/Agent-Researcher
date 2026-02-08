"""
Example usage of Web Scraper Engine
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.nodes.web_scraper import WebScraperEngine


def example_basic_scraping():
    """Basic scraping example"""
    print("=" * 80)
    print("Example 1: Basic Web Scraping")
    print("=" * 80)
    
    # Initialize engine with default config
    scraper = WebScraperEngine()
    
    # Prepare URL batch
    url_batch = [
        {
            "url": "https://en.wikipedia.org/wiki/Web_scraping",
            "domain": "en.wikipedia.org",
            "credibility_score": 0.95,
            "robots_allowed": True,
            "source_type": "web",
            "validation_timestamp": "2024-01-15T10:00:00Z",
            "metadata": {
                "title_extracted": "Web scraping",
                "content_type": "text/html",
                "estimated_size_kb": 150
            }
        },
        {
            "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "domain": "en.wikipedia.org",
            "credibility_score": 0.95,
            "robots_allowed": True,
            "source_type": "web",
            "validation_timestamp": "2024-01-15T10:00:00Z",
            "metadata": {}
        }
    ]
    
    # Scrape URLs
    result = scraper.scrape_urls(
        url_batch=url_batch,
        batch_id="example_batch_001",
        priority_level=1
    )
    
    # Display results
    print(f"\nStatus: {result['status']}")
    print(f"Processing time: {result['processing_time_ms']}ms")
    print(f"URLs processed: {len(result['data']['scraped_data'])}")
    
    # Show extracted content
    for item in result['data']['scraped_data']:
        print(f"\n{'='*80}")
        print(f"URL: {item['source_url']}")
        print(f"Title: {item['extracted_content'].get('title', 'N/A')}")
        print(f"Text length: {len(item['extracted_content'].get('text', ''))}")
        print(f"Language: {item['extracted_content'].get('metadata', {}).get('language_detected', 'N/A')}")
        print(f"Readability: {item['extracted_content'].get('metadata', {}).get('readability_score', 'N/A')}")
        print(f"Sentiment: {item['extracted_content'].get('metadata', {}).get('sentiment', 'N/A')}")
        print(f"Parser used: {item['scraping_metadata']['parser_used']}")
        print(f"Extraction confidence: {item['scraping_metadata']['extraction_confidence']:.2f}")
        
        # Show first 200 characters of text
        text = item['extracted_content'].get('text', '')
        if text:
            print(f"\nFirst 200 chars: {text[:200]}...")
    
    # Show batch statistics
    print(f"\n{'='*80}")
    print("Batch Statistics:")
    stats = result['data']['batch_statistics']
    print(f"  Total URLs processed: {stats['total_urls_processed']}")
    print(f"  Successful scrapes: {stats['successful_scrapes']}")
    print(f"  Failed scrapes: {stats['failed_scrapes']}")
    print(f"  Total data extracted: {stats['total_data_extracted_bytes']:,} bytes")
    
    return result


def example_with_custom_config():
    """Example with custom configuration"""
    print("\n" + "=" * 80)
    print("Example 2: Custom Configuration")
    print("=" * 80)
    
    # Custom config
    config = {
        'default_delay_seconds': 2.0,
        'max_concurrent_requests': 3,
        'enable_caching': True,
        'cache_ttl_hours': 48,
        'min_content_length_chars': 200,
        'preserve_structure': True,
        'discover_new_links': True,
        'same_domain_only': True
    }
    
    scraper = WebScraperEngine(config=config)
    
    # Scrape with custom config
    url_batch = [
        {
            "url": "https://github.com/python/cpython",
            "domain": "github.com",
            "credibility_score": 0.98,
            "robots_allowed": True,
            "source_type": "web",
            "validation_timestamp": "2024-01-15T10:00:00Z",
            "metadata": {}
        }
    ]
    
    result = scraper.scrape_urls(
        url_batch=url_batch,
        batch_id="example_batch_002",
        priority_level=2
    )
    
    print(f"\nStatus: {result['status']}")
    print(f"Processing time: {result['processing_time_ms']}ms")
    
    if result['data']['scraped_data']:
        item = result['data']['scraped_data'][0]
        print(f"\nTitle: {item['extracted_content'].get('title', 'N/A')}")
        print(f"Discovered links: {len(item.get('discovered_links', []))}")
        
        # Show some discovered links
        links = item.get('discovered_links', [])[:5]
        if links:
            print("\nFirst 5 discovered links:")
            for link in links:
                print(f"  - {link['url']}")
                print(f"    Anchor: {link.get('anchor_text', 'N/A')}")
                print(f"    Context: {link.get('discovery_context', 'N/A')}")
    
    return result


def example_with_custom_patterns():
    """Example with custom extraction patterns"""
    print("\n" + "=" * 80)
    print("Example 3: Custom Extraction Patterns")
    print("=" * 80)
    
    scraper = WebScraperEngine()
    
    # Custom extraction patterns for Wikipedia
    extraction_patterns = {
        "main_content": "#mw-content-text",
        "title": "#firstHeading",
        "categories": ".mw-normal-catlinks a"
    }
    
    url_batch = [
        {
            "url": "https://en.wikipedia.org/wiki/Machine_learning",
            "domain": "en.wikipedia.org",
            "credibility_score": 0.95,
            "robots_allowed": True,
            "source_type": "web",
            "validation_timestamp": "2024-01-15T10:00:00Z",
            "metadata": {}
        }
    ]
    
    result = scraper.scrape_urls(
        url_batch=url_batch,
        extraction_patterns=extraction_patterns,
        batch_id="example_batch_003",
        priority_level=1
    )
    
    print(f"\nStatus: {result['status']}")
    
    if result['data']['scraped_data']:
        item = result['data']['scraped_data'][0]
        print(f"\nTitle: {item['extracted_content'].get('title', 'N/A')}")
        print(f"Parser used: {item['scraping_metadata']['parser_used']}")
        print(f"Extraction confidence: {item['scraping_metadata']['extraction_confidence']:.2f}")
    
    return result


def example_metrics():
    """Example showing metrics"""
    print("\n" + "=" * 80)
    print("Example 4: Monitoring Metrics")
    print("=" * 80)
    
    scraper = WebScraperEngine()
    
    # Scrape a few URLs
    url_batch = [
        {
            "url": "https://en.wikipedia.org/wiki/Data_science",
            "domain": "en.wikipedia.org",
            "credibility_score": 0.95,
            "robots_allowed": True,
            "source_type": "web",
            "validation_timestamp": "2024-01-15T10:00:00Z",
            "metadata": {}
        }
    ]
    
    result = scraper.scrape_urls(url_batch=url_batch)
    
    # Get metrics
    metrics = scraper.get_metrics()
    
    print("\nEngine Metrics:")
    print(json.dumps(metrics['stats'], indent=2))
    
    if 'cache' in metrics and metrics['cache']:
        print("\nCache Metrics:")
        print(json.dumps(metrics['cache'], indent=2))
    
    return metrics


if __name__ == "__main__":
    print("\n" + "="*80)
    print(" Web Scraper Engine - Example Usage")
    print("="*80 + "\n")
    
    try:
        # Run examples
        example_basic_scraping()
        # example_with_custom_config()
        # example_with_custom_patterns()
        # example_metrics()
        
        print("\n" + "="*80)
        print("All examples completed successfully!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()