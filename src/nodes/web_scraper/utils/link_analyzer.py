 
"""
Link extraction and analysis utilities
"""
from typing import List, Dict, Optional, Set
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import re


class LinkAnalyzer:
    """
    Analyzes and extracts links from HTML content
    """
    
    # Link types to ignore
    IGNORE_SCHEMES = {'mailto', 'tel', 'javascript', 'data'}
    
    # Common navigation patterns
    NAV_PATTERNS = [
        r'nav(igation)?', r'menu', r'header', r'footer', r'sidebar',
        r'breadcrumb', r'pagination'
    ]
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.seen_urls: Set[str] = set()
    
    def extract_links(
        self,
        html: str,
        filter_same_domain: bool = False,
        exclude_navigation: bool = True
    ) -> List[Dict[str, any]]:
        """
        Extract all links from HTML
        
        Args:
            html: HTML string
            filter_same_domain: Only return links from same domain
            exclude_navigation: Exclude navigation links
            
        Returns:
            List of link dictionaries with metadata
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        links = []
        
        # Remove navigation elements if requested
        if exclude_navigation:
            for pattern in self.NAV_PATTERNS:
                for element in soup.find_all(class_=re.compile(pattern, re.I)):
                    element.decompose()
                for element in soup.find_all(id=re.compile(pattern, re.I)):
                    element.decompose()
        
        # Extract all <a> tags
        for link_tag in soup.find_all('a', href=True):
            href = link_tag.get('href', '').strip()
            
            if not href or href.startswith('#'):
                continue
            
            # Build absolute URL
            absolute_url = urljoin(self.base_url, href)
            
            # Check scheme
            parsed = urlparse(absolute_url)
            if parsed.scheme in self.IGNORE_SCHEMES:
                continue
            
            # Filter by domain if requested
            if filter_same_domain:
                base_domain = urlparse(self.base_url).netloc
                if parsed.netloc != base_domain:
                    continue
            
            # Skip if already seen
            if absolute_url in self.seen_urls:
                continue
            
            self.seen_urls.add(absolute_url)
            
            # Extract link metadata
            link_data = {
                'url': absolute_url,
                'anchor_text': link_tag.get_text(strip=True) or None,
                'title': link_tag.get('title') or None,
                'rel': link_tag.get('rel') or [],
                'is_nofollow': 'nofollow' in (link_tag.get('rel') or []),
                'discovery_context': self._get_context(link_tag)
            }
            
            links.append(link_data)
        
        return links
    
    def _get_context(self, link_tag) -> str:
        """Determine the context where link was found"""
        # Check parent tags
        parents = [p.name for p in link_tag.parents]
        
        if 'article' in parents or 'main' in parents:
            return 'main_content'
        elif 'nav' in parents:
            return 'navigation'
        elif 'footer' in parents:
            return 'footer'
        elif 'aside' in parents or 'sidebar' in parents:
            return 'sidebar'
        else:
            return 'other'
    
    def categorize_links(self, links: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize links by type
        
        Args:
            links: List of link dictionaries
            
        Returns:
            Dictionary of categorized links
        """
        categories = {
            'internal': [],
            'external': [],
            'media': [],
            'documents': [],
            'social': []
        }
        
        base_domain = urlparse(self.base_url).netloc
        
        for link in links:
            url = link['url']
            parsed = urlparse(url)
            
            # Internal vs external
            if parsed.netloc == base_domain:
                categories['internal'].append(link)
            else:
                categories['external'].append(link)
            
            # Media files
            if re.search(r'\.(jpg|jpeg|png|gif|webp|svg|mp4|mp3|avi|mov)$', 
                        url, re.I):
                categories['media'].append(link)
            
            # Documents
            if re.search(r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv)$',
                        url, re.I):
                categories['documents'].append(link)
            
            # Social media
            social_domains = ['facebook.com', 'twitter.com', 'x.com', 
                            'instagram.com', 'linkedin.com', 'youtube.com']
            if any(domain in parsed.netloc for domain in social_domains):
                categories['social'].append(link)
        
        return categories
    
    def detect_pagination(self, html: str) -> Optional[Dict]:
        """
        Detect pagination patterns
        
        Args:
            html: HTML string
            
        Returns:
            Dictionary with pagination info or None
        """
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        pagination = {}
        
        # Look for common pagination patterns
        pagination_selectors = [
            ('next', ['a[rel="next"]', '.next', '.pagination-next', 
                     'a:contains("Next")', 'a:contains("→")']),
            ('prev', ['a[rel="prev"]', '.prev', '.pagination-prev',
                     'a:contains("Previous")', 'a:contains("←")']),
            ('pages', ['.pagination a', '.pager a', 'nav[role="navigation"] a'])
        ]
        
        for key, selectors in pagination_selectors:
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    if key == 'pages':
                        pagination[key] = [
                            urljoin(self.base_url, elem.get('href', ''))
                            for elem in elements if elem.get('href')
                        ]
                    else:
                        elem = elements[0]
                        href = elem.get('href')
                        if href:
                            pagination[key] = urljoin(self.base_url, href)
                    break
        
        return pagination if pagination else None
    
    def score_link_relevance(
        self,
        link: Dict,
        keywords: Optional[List[str]] = None
    ) -> float:
        """
        Score link relevance based on anchor text and context
        
        Args:
            link: Link dictionary
            keywords: List of keywords to check for
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.5  # Base score
        
        # Boost for main content links
        if link.get('discovery_context') == 'main_content':
            score += 0.2
        
        # Penalize navigation and footer links
        if link.get('discovery_context') in ['navigation', 'footer']:
            score -= 0.2
        
        # Penalize nofollow links
        if link.get('is_nofollow'):
            score -= 0.1
        
        # Check for keywords in anchor text
        if keywords and link.get('anchor_text'):
            anchor_lower = link['anchor_text'].lower()
            keyword_matches = sum(1 for kw in keywords if kw.lower() in anchor_lower)
            score += min(0.3, keyword_matches * 0.1)
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def clear_seen_urls(self):
        """Clear the set of seen URLs"""
        self.seen_urls.clear()