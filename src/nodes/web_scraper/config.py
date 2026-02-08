"""
Domain-specific extraction rules and patterns
"""

DOMAIN_RULES = {
    "wikipedia.org": {
        "extraction_patterns": {
            "main_content": "#mw-content-text",
            "title": "#firstHeading",
            "categories": ".mw-normal-catlinks a"
        },
        "rate_limit": 0.5,
        "requires_javascript": False
    },
    "twitter.com": {
        "extraction_patterns": {
            "main_content": "article[data-testid='tweet']",
            "author": "div[data-testid='User-Name']",
            "date": "time"
        },
        "requires_javascript": True,
        "rate_limit": 2.0
    },
    "x.com": {
        "extraction_patterns": {
            "main_content": "article[data-testid='tweet']",
            "author": "div[data-testid='User-Name']",
            "date": "time"
        },
        "requires_javascript": True,
        "rate_limit": 2.0
    },
    "arxiv.org": {
        "extraction_patterns": {
            "main_content": ".ltx_page_content",
            "title": ".ltx_title",
            "authors": ".ltx_personname",
            "abstract": ".ltx_abstract"
        },
        "prefer_pdf": True,
        "rate_limit": 1.0,
        "requires_javascript": False
    },
    "github.com": {
        "extraction_patterns": {
            "main_content": ".repository-content",
            "title": ".js-repo-title",
            "readme": "#readme"
        },
        "rate_limit": 1.0,
        "requires_javascript": False
    },
    "medium.com": {
        "extraction_patterns": {
            "main_content": "article",
            "title": "h1",
            "author": "a[rel='author']"
        },
        "rate_limit": 1.5,
        "requires_javascript": True
    },
    "reddit.com": {
        "extraction_patterns": {
            "main_content": "[data-test-id='post-content']",
            "title": "h1",
            "author": "[data-testid='post_author_link']"
        },
        "rate_limit": 2.0,
        "requires_javascript": True
    },
    "stackoverflow.com": {
        "extraction_patterns": {
            "main_content": ".question, .answer",
            "title": ".question-hyperlink",
            "code": "pre code"
        },
        "rate_limit": 0.5,
        "requires_javascript": False
    },
    "news.ycombinator.com": {
        "extraction_patterns": {
            "main_content": ".fatitem",
            "title": ".titleline a",
            "comments": ".comment"
        },
        "rate_limit": 1.0,
        "requires_javascript": False
    }
}


def get_domain_rules(domain: str) -> dict:
    """
    Get extraction rules for a specific domain
    
    Args:
        domain: Domain name (e.g., 'example.com')
        
    Returns:
        Dictionary with extraction patterns and settings
    """
    # Try exact match first
    if domain in DOMAIN_RULES:
        return DOMAIN_RULES[domain]
    
    # Try to match without subdomain
    for rule_domain, rules in DOMAIN_RULES.items():
        if domain.endswith(rule_domain):
            return rules
    
    # Return default rules
    return {
        "extraction_patterns": {},
        "rate_limit": 1.0,
        "requires_javascript": False,
        "prefer_pdf": False
    }