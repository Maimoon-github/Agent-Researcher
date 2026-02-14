"""
Source Discovery Agent - Practical Usage Examples
=================================================

This file contains practical examples demonstrating different use cases
and configurations of the Source Discovery Agent.
"""

from source_discovery_agent import (
    SourceDiscoveryInput,
    CredibilityRequirements,
    run_source_discovery,
)


# =============================================================================
# EXAMPLE 1: Academic Research
# =============================================================================

def example_academic_research():
    """
    High-rigor academic research requiring trusted sources.
    Use case: Literature review for a research paper
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Academic Research")
    print("=" * 80 + "\n")
    
    input_data = SourceDiscoveryInput(
        topic="transformer architecture in natural language processing",
        max_results=20,
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.8,  # High authority only
            max_age_days=730,  # Last 2 years
            trusted_domains=[
                'edu',           # Universities
                'gov',           # Government
                'arxiv.org',     # arXiv preprints
                'ieee.org',      # IEEE
                'acm.org',       # ACM
                'nature.com',    # Nature journals
                'science.org'    # Science journals
            ],
            require_https=True,
            min_relevance_score=0.6  # Highly relevant only
        )
    )
    
    output = run_source_discovery(input_data)
    
    print(f"Found {output.total_validated} high-quality academic sources")
    print(f"Average authority score: {sum(s.domain_authority_score for s in output.sources) / len(output.sources):.2f}")
    
    # Display academic sources
    for i, source in enumerate(output.sources[:5], 1):
        print(f"\n{i}. {source.title}")
        print(f"   Domain: {source.domain} (Authority: {source.domain_authority_score:.2f})")
        print(f"   URL: {source.url}")


# =============================================================================
# EXAMPLE 2: News Monitoring
# =============================================================================

def example_news_monitoring():
    """
    Monitor recent news on a topic.
    Use case: Track breaking developments in a field
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: News Monitoring")
    print("=" * 80 + "\n")
    
    input_data = SourceDiscoveryInput(
        topic="artificial intelligence regulation EU",
        max_results=15,
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.6,
            max_age_days=30,  # Last month only
            required_content_types=['news', 'article'],
            require_https=True,
            min_relevance_score=0.5
        )
    )
    
    output = run_source_discovery(input_data)
    
    print(f"Found {output.total_validated} recent news articles")
    
    # Group by domain
    domains = {}
    for source in output.sources:
        if source.domain not in domains:
            domains[source.domain] = []
        domains[source.domain].append(source)
    
    print(f"\nCoverage from {len(domains)} different news sources:")
    for domain, sources in sorted(domains.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {domain}: {len(sources)} articles")


# =============================================================================
# EXAMPLE 3: General Web Research
# =============================================================================

def example_general_research():
    """
    General web research with moderate requirements.
    Use case: Background research on a new topic
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: General Web Research")
    print("=" * 80 + "\n")
    
    input_data = SourceDiscoveryInput(
        topic="sustainable agriculture vertical farming",
        max_results=15,
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.5,  # Moderate threshold
            max_age_days=1095,  # Last 3 years
            require_https=False,  # Allow HTTP
            min_relevance_score=0.3  # More permissive
        )
    )
    
    output = run_source_discovery(input_data)
    
    print(f"Found {output.total_validated} diverse sources")
    
    # Categorize by content type
    by_type = {}
    for source in output.sources:
        content_type = source.content_type
        if content_type not in by_type:
            by_type[content_type] = []
        by_type[content_type].append(source)
    
    print("\nContent types discovered:")
    for content_type, sources in by_type.items():
        print(f"  {content_type}: {len(sources)} sources")


# =============================================================================
# EXAMPLE 4: Technical Documentation Search
# =============================================================================

def example_technical_docs():
    """
    Search for technical documentation and tutorials.
    Use case: Learning a new technology or framework
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Technical Documentation Search")
    print("=" * 80 + "\n")
    
    input_data = SourceDiscoveryInput(
        topic="LangGraph multi-agent systems tutorial",
        max_results=10,
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.6,
            trusted_domains=[
                'python.org',
                'langchain.com',
                'github.com',
                'readthedocs.io',
                'medium.com',
                'towardsdatascience.com'
            ],
            require_https=True,
            min_relevance_score=0.5
        )
    )
    
    output = run_source_discovery(input_data)
    
    print(f"Found {output.total_validated} technical resources")
    
    # Prioritize official documentation
    official_docs = [s for s in output.sources if any(
        domain in s.domain for domain in ['langchain', 'readthedocs', 'python.org']
    )]
    
    print(f"\nOfficial documentation: {len(official_docs)} sources")
    for source in official_docs:
        print(f"  - {source.title}")
        print(f"    {source.url}")


# =============================================================================
# EXAMPLE 5: Competitive Intelligence
# =============================================================================

def example_competitive_intelligence():
    """
    Gather information about competitors or market trends.
    Use case: Market research and competitive analysis
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Competitive Intelligence")
    print("=" * 80 + "\n")
    
    input_data = SourceDiscoveryInput(
        topic="AI chatbot market trends 2024",
        max_results=20,
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.6,
            max_age_days=180,  # Last 6 months
            trusted_domains=[
                'gartner.com',
                'forrester.com',
                'techcrunch.com',
                'venturebeat.com',
                'bloomberg.com',
                'forbes.com'
            ],
            require_https=True,
            min_relevance_score=0.4
        )
    )
    
    output = run_source_discovery(input_data)
    
    print(f"Found {output.total_validated} market intelligence sources")
    
    # Sort by authority and recency
    recent_high_authority = sorted(
        output.sources,
        key=lambda s: (s.domain_authority_score, s.last_updated or datetime.min),
        reverse=True
    )
    
    print("\nTop authoritative recent sources:")
    for source in recent_high_authority[:5]:
        age = "N/A"
        if source.last_updated:
            days_old = (datetime.utcnow() - source.last_updated).days
            age = f"{days_old} days ago"
        
        print(f"\n  {source.title}")
        print(f"  Authority: {source.domain_authority_score:.2f} | Age: {age}")
        print(f"  {source.url}")


# =============================================================================
# EXAMPLE 6: Multi-Language Research
# =============================================================================

def example_multilingual_research():
    """
    Search in different languages.
    Use case: International market research or cross-cultural studies
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Multi-Language Research")
    print("=" * 80 + "\n")
    
    # Search in Spanish
    input_data_es = SourceDiscoveryInput(
        topic="inteligencia artificial ética",
        max_results=10,
        language="es",  # Spanish
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.5,
            require_https=True,
            min_relevance_score=0.4
        )
    )
    
    output_es = run_source_discovery(input_data_es)
    
    print(f"Spanish sources found: {output_es.total_validated}")
    
    # Search in German
    input_data_de = SourceDiscoveryInput(
        topic="künstliche intelligenz ethik",
        max_results=10,
        language="de",  # German
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.5,
            require_https=True,
            min_relevance_score=0.4
        )
    )
    
    output_de = run_source_discovery(input_data_de)
    
    print(f"German sources found: {output_de.total_validated}")


# =============================================================================
# EXAMPLE 7: Custom Validation Pipeline
# =============================================================================

def example_custom_validation():
    """
    Implement custom post-validation filtering.
    Use case: Apply domain-specific quality criteria
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Custom Validation Pipeline")
    print("=" * 80 + "\n")
    
    input_data = SourceDiscoveryInput(
        topic="climate change mitigation strategies",
        max_results=20,
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.6,
            max_age_days=365,
            require_https=True
        )
    )
    
    output = run_source_discovery(input_data)
    
    # Custom filtering: Only sources with certain keywords
    required_keywords = ['climate', 'carbon', 'emissions', 'sustainability']
    
    filtered_sources = []
    for source in output.sources:
        # Check if source has at least 2 required keywords
        keyword_matches = sum(
            1 for kw in required_keywords 
            if any(kw in sk.lower() for sk in source.keywords)
        )
        
        if keyword_matches >= 2:
            filtered_sources.append(source)
    
    print(f"After custom filtering: {len(filtered_sources)}/{output.total_validated} sources")
    
    # Calculate average scores
    if filtered_sources:
        avg_authority = sum(s.domain_authority_score for s in filtered_sources) / len(filtered_sources)
        avg_relevance = sum(s.relevance_score for s in filtered_sources) / len(filtered_sources)
        
        print(f"Average authority: {avg_authority:.2f}")
        print(f"Average relevance: {avg_relevance:.2f}")


# =============================================================================
# EXAMPLE 8: Batch Processing Multiple Topics
# =============================================================================

def example_batch_processing():
    """
    Process multiple research topics in batch.
    Use case: Systematic literature review across multiple subtopics
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 8: Batch Processing Multiple Topics")
    print("=" * 80 + "\n")
    
    topics = [
        "reinforcement learning robotics",
        "computer vision object detection",
        "natural language processing transformers",
        "generative adversarial networks applications"
    ]
    
    all_sources = {}
    
    for topic in topics:
        print(f"\nProcessing: {topic}")
        
        input_data = SourceDiscoveryInput(
            topic=topic,
            max_results=10,
            credibility_requirements=CredibilityRequirements(
                min_domain_authority=0.7,
                max_age_days=365,
                require_https=True
            )
        )
        
        output = run_source_discovery(input_data)
        all_sources[topic] = output.sources
        
        print(f"  Found {output.total_validated} sources")
    
    # Aggregate statistics
    total_sources = sum(len(sources) for sources in all_sources.values())
    unique_domains = set()
    for sources in all_sources.values():
        unique_domains.update(s.domain for s in sources)
    
    print(f"\n{'='*80}")
    print(f"Batch Summary:")
    print(f"  Topics processed: {len(topics)}")
    print(f"  Total sources: {total_sources}")
    print(f"  Unique domains: {len(unique_domains)}")
    print(f"  Average per topic: {total_sources / len(topics):.1f}")


# =============================================================================
# EXAMPLE 9: Export Results to Different Formats
# =============================================================================

def example_export_results():
    """
    Export results to various formats.
    Use case: Integration with other tools and workflows
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 9: Export Results")
    print("=" * 80 + "\n")
    
    input_data = SourceDiscoveryInput(
        topic="quantum computing applications",
        max_results=10,
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.7
        )
    )
    
    output = run_source_discovery(input_data)
    
    # Export to JSON
    import json
    json_output = output.model_dump_json(indent=2)
    print("JSON export created (first 500 chars):")
    print(json_output[:500] + "...")
    
    # Export to CSV format
    print("\nCSV format:")
    print("URL,Title,Domain,Authority,Relevance,Type")
    for source in output.sources[:5]:
        print(f'"{source.url}","{source.title}","{source.domain}",'
              f'{source.domain_authority_score:.2f},{source.relevance_score:.2f},'
              f'{source.content_type}')
    
    # Export to Markdown
    print("\nMarkdown format:")
    for i, source in enumerate(output.sources[:5], 1):
        print(f"\n{i}. [{source.title}]({source.url})")
        print(f"   - **Domain**: {source.domain}")
        print(f"   - **Authority**: {source.domain_authority_score:.2f}")
        print(f"   - **Relevance**: {source.relevance_score:.2f}")


# =============================================================================
# EXAMPLE 10: Progressive Filtering Strategy
# =============================================================================

def example_progressive_filtering():
    """
    Use progressive filtering to find the best sources.
    Use case: When you need highest quality sources but want to see the funnel
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 10: Progressive Filtering")
    print("=" * 80 + "\n")
    
    # Start with lenient requirements
    input_data = SourceDiscoveryInput(
        topic="blockchain consensus algorithms",
        max_results=30,
        credibility_requirements=CredibilityRequirements(
            min_domain_authority=0.3,  # Very lenient
            max_age_days=1825,  # 5 years
            require_https=False,
            min_relevance_score=0.2
        )
    )
    
    output = run_source_discovery(input_data)
    
    print(f"Stage 1 - Broad search: {output.total_validated} sources")
    
    # Progressive filtering
    stages = [
        ("Stage 2 - Authority > 0.5", lambda s: s.domain_authority_score > 0.5),
        ("Stage 3 - Authority > 0.7", lambda s: s.domain_authority_score > 0.7),
        ("Stage 4 - Authority > 0.7 AND Relevance > 0.5", 
         lambda s: s.domain_authority_score > 0.7 and s.relevance_score > 0.5),
        ("Stage 5 - Authority > 0.8 AND Relevance > 0.6 AND HTTPS",
         lambda s: s.domain_authority_score > 0.8 and s.relevance_score > 0.6 and s.is_https),
    ]
    
    current_sources = output.sources
    
    for stage_name, filter_func in stages:
        current_sources = [s for s in current_sources if filter_func(s)]
        print(f"{stage_name}: {len(current_sources)} sources")
    
    print(f"\nFinal high-quality sources: {len(current_sources)}")
    for source in current_sources[:3]:
        print(f"\n  {source.title}")
        print(f"  Authority: {source.domain_authority_score:.2f} | "
              f"Relevance: {source.relevance_score:.2f}")


# =============================================================================
# MAIN - RUN ALL EXAMPLES
# =============================================================================

if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    print("\n" + "=" * 80)
    print("SOURCE DISCOVERY AGENT - PRACTICAL EXAMPLES")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    examples = [
        ("Academic Research", example_academic_research),
        ("News Monitoring", example_news_monitoring),
        ("General Research", example_general_research),
        ("Technical Documentation", example_technical_docs),
        ("Competitive Intelligence", example_competitive_intelligence),
        ("Multi-Language Research", example_multilingual_research),
        ("Custom Validation", example_custom_validation),
        ("Batch Processing", example_batch_processing),
        ("Export Results", example_export_results),
        ("Progressive Filtering", example_progressive_filtering),
    ]
    
    # Allow running specific example from command line
    if len(sys.argv) > 1:
        try:
            example_num = int(sys.argv[1])
            if 1 <= example_num <= len(examples):
                name, func = examples[example_num - 1]
                print(f"\nRunning Example {example_num}: {name}")
                func()
            else:
                print(f"Error: Example number must be between 1 and {len(examples)}")
        except ValueError:
            print("Error: Please provide a valid example number")
        except Exception as e:
            print(f"Error running example: {e}")
            import traceback
            traceback.print_exc()
    else:
        # Run all examples
        print("\nRunning all examples...")
        print("(This may take several minutes due to rate limiting)")
        print("\nTo run a specific example, use: python examples.py <number>")
        print("For example: python examples.py 1")
        
        for i, (name, func) in enumerate(examples, 1):
            print(f"\n{'='*80}")
            print(f"Running Example {i}/{len(examples)}: {name}")
            print(f"{'='*80}")
            try:
                func()
            except Exception as e:
                print(f"\nError in example {i}: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")
