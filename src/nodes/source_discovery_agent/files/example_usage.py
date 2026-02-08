#!/usr/bin/env python3
"""
Example usage of the Source Discovery Agent

This script demonstrates various ways to use the Source Discovery Agent
for research query processing and source validation.
"""

import json
import sys
import os

# Add project root to sys.path to allow absolute imports
# This file is in: src/nodes/source_discovery_agent/files/example_usage.py
# Root is at: ../../../..
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.nodes.source_discovery_agent import SourceDiscoveryAgent, SourceDiscoveryConfig


def example_basic_usage():
    """Example 1: Basic usage with default configuration"""
    print("\n" + "="*80)
    print("Example 1: Basic Usage")
    print("="*80 + "\n")
    
    # Initialize agent with defaults
    agent = SourceDiscoveryAgent()
    
    # Discover sources
    result = agent.discover_sources(
        query="Impact of climate change on biodiversity"
    )
    
    # Display results
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        data = result['data']
        print(f"Search terms: {', '.join(data['search_terms'])}")
        print(f"Sources found: {len(data['validated_urls'])}")
        print(f"Processing time: {result['processing_time_ms']}ms")
        
        # Display top 3 sources
        print("\nTop 3 sources:")
        for i, source in enumerate(data['validated_urls'][:3], 1):
            print(f"{i}. {source['domain']} (credibility: {source['credibility_score']:.2f})")
    else:
        print(f"Error: {result['error']['message']}")


def example_custom_configuration():
    """Example 2: Custom configuration"""
    print("\n" + "="*80)
    print("Example 2: Custom Configuration")
    print("="*80 + "\n")
    
    # Create custom configuration
    config = SourceDiscoveryConfig(
        min_credibility_score=0.8,
        max_urls_per_domain=3,
        request_timeout_seconds=15,
        enable_wayback_check=False,
        cache_validation_results=True
    )
    
    # Initialize agent with custom config
    agent = SourceDiscoveryAgent(config=config)
    
    # Discover sources
    result = agent.discover_sources(
        query="Machine learning in healthcare",
        source_type_preferences=["academic", "technical"],
        max_sources_per_type=5
    )
    
    if result['status'] == 'success':
        data = result['data']
        print(f"Sources found: {len(data['validated_urls'])}")
        
        # Display credibility distribution
        dist = data['discovery_metrics']['credibility_score_distribution']
        print(f"\nCredibility distribution:")
        print(f"  Min: {dist['min']:.2f}")
        print(f"  Max: {dist['max']:.2f}")
        print(f"  Average: {dist['average']:.2f}")
        print(f"  Median: {dist['median']:.2f}")


def example_academic_research():
    """Example 3: Academic research query"""
    print("\n" + "="*80)
    print("Example 3: Academic Research Query")
    print("="*80 + "\n")
    
    agent = SourceDiscoveryAgent()
    
    result = agent.discover_sources(
        query="peer-reviewed research on quantum computing",
        source_type_preferences=["academic"],
        credibility_threshold=0.85,
        max_sources_per_type=10
    )
    
    if result['status'] == 'success':
        data = result['data']
        
        # Display source types
        print(f"Source types identified: {', '.join(data['source_types_identified'])}")
        
        # Display recommendations
        recommendations = data['recommendations']
        print(f"\nPrimary source clusters: {', '.join(recommendations['primary_source_clusters'])}")
        print(f"Coverage gaps: {', '.join(recommendations['coverage_gaps']) if recommendations['coverage_gaps'] else 'None'}")
        print(f"Confidence level: {recommendations['confidence_level']:.2%}")


def example_error_handling():
    """Example 4: Error handling"""
    print("\n" + "="*80)
    print("Example 4: Error Handling")
    print("="*80 + "\n")
    
    agent = SourceDiscoveryAgent()
    
    # Try with an invalid query
    result = agent.discover_sources(query="ab")  # Too short
    
    if result['status'] == 'error':
        error = result['error']
        print(f"Error type: {error['type']}")
        print(f"Error code: {error['code']}")
        print(f"Message: {error['message']}")
        print(f"\nSuggestions:")
        for suggestion in error['suggestions']:
            print(f"  - {suggestion}")


def example_metrics_collection():
    """Example 5: Metrics collection"""
    print("\n" + "="*80)
    print("Example 5: Metrics Collection")
    print("="*80 + "\n")
    
    agent = SourceDiscoveryAgent()
    
    # Process multiple queries
    queries = [
        "artificial intelligence ethics",
        "renewable energy technologies",
        "COVID-19 vaccine development"
    ]
    
    for query in queries:
        result = agent.discover_sources(query, max_sources_per_type=30, credibility_threshold=0.6)
        print(f"Processed: {query}")
    
    # Get aggregated metrics
    metrics = agent.get_metrics()
    
    print(f"\n{json.dumps(metrics, indent=2)}")


def example_detailed_source_info():
    """Example 6: Detailed source information"""
    print("\n" + "="*80)
    print("Example 6: Detailed Source Information")
    print("="*80 + "\n")
    
    agent = SourceDiscoveryAgent()
    
    result = agent.discover_sources(
        query="blockchain technology applications",
        max_sources_per_type=3
    )
    
    if result['status'] == 'success':
        print("Detailed source information:\n")
        
        for source in result['data']['validated_urls'][:3]:
            print(f"URL: {source['url']}")
            print(f"  Domain: {source['domain']}")
            print(f"  Credibility Score: {source['credibility_score']:.2f}")
            print(f"  Source Type: {source['source_type']}")
            print(f"  Robots Allowed: {source['robots_allowed']}")
            
            metadata = source['metadata']
            print(f"  Content Type: {metadata['content_type']}")
            if metadata['estimated_size_kb']:
                print(f"  Size: {metadata['estimated_size_kb']} KB")
            print()


def example_full_workflow():
    """Example 7: Full research workflow"""
    print("\n" + "="*80)
    print("Example 7: Full Research Workflow")
    print("="*80 + "\n")
    
    # Configure agent
    config = SourceDiscoveryConfig(
        min_credibility_score=0.6,
        max_urls_per_domain=10,
        local_scan_directories=["/tmp"],  # Example directory
        enable_cross_referencing=True
    )
    
    agent = SourceDiscoveryAgent(config=config)
    
    # Define research query
    query = "sustainable agriculture practices in developing countries"
    
    print(f"Research Query: {query}\n")
    
    # Discover sources
    result = agent.discover_sources(
        query=query,
        query_id="research_001",
        source_type_preferences=["web", "academic", "news"],
        credibility_threshold=0.6,
        max_sources_per_type=30
    )
    
    if result['status'] == 'success':
        data = result['data']
        
        print("="*80)
        print("DISCOVERY RESULTS")
        print("="*80)
        
        # Summary
        print(f"\nQuery ID: {result['query_id']}")
        print(f"Processing Time: {result['processing_time_ms']}ms")
        print(f"Status: {result['status']}")
        
        # Metrics
        metrics = data['discovery_metrics']
        print(f"\nSources Considered: {metrics['total_sources_considered']}")
        print(f"Sources Validated: {metrics['validated_sources_count']}")
        print(f"Validation Failures: {metrics['validation_failures']}")
        
        # Source breakdown
        print(f"\nSource Types: {', '.join(data['source_types_identified'])}")
        
        # Recommendations
        recommendations = data['recommendations']
        print(f"\nTop Domains: {', '.join(recommendations['primary_source_clusters'][:5])}")
        print(f"Confidence Level: {recommendations['confidence_level']:.1%}")
        
        if recommendations['coverage_gaps']:
            print(f"Coverage Gaps: {', '.join(recommendations['coverage_gaps'])}")
        
        # Warnings
        if result.get('warnings'):
            print(f"\nWarnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")
        
        # Export URLs for downstream processing
        urls = [source['url'] for source in data['validated_urls']]
        print(f"\n{len(urls)} URLs ready for downstream processing")
        
    else:
        print(f"Discovery failed: {result['error']['message']}")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("SOURCE DISCOVERY AGENT - EXAMPLE USAGE")
    print("="*80)
    
    examples = [
        example_basic_usage,
        example_custom_configuration,
        example_academic_research,
        example_error_handling,
        example_metrics_collection,
        example_detailed_source_info,
        example_full_workflow
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\nError in {example_func.__name__}: {str(e)}")
    
    print("\n" + "="*80)
    print("EXAMPLES COMPLETED")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
