 
"""
URL normalization and validation utilities
"""
import re
from urllib.parse import urlparse, urlunparse, urljoin, parse_qs, urlencode
from typing import Optional
import validators


class URLNormalizer:
    """
    Normalizes and validates URLs
    """
    
    # Common tracking parameters to remove
    TRACKING_PARAMS = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'msclkid', 'mc_cid', 'mc_eid',
        '_ga', '_gl', 'ref', 'source'
    }
    
    # Fragment identifiers that should be kept
    KEEP_FRAGMENTS = {'!', '#!/'}
    
    def __init__(self, remove_tracking: bool = True, remove_fragments: bool = True):
        self.remove_tracking = remove_tracking
        self.remove_fragments = remove_fragments
    
    def normalize(self, url: str, base_url: Optional[str] = None) -> Optional[str]:
        """
        Normalize a URL
        
        Args:
            url: URL to normalize
            base_url: Base URL for relative URLs
            
        Returns:
            Normalized URL or None if invalid
        """
        if not url or not isinstance(url, str):
            return None
        
        # Handle relative URLs
        if base_url and not url.startswith(('http://', 'https://', '//')):
            url = urljoin(base_url, url)
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception:
            return None
        
        # Ensure scheme is present
        if not parsed.scheme:
            if url.startswith('//'):
                url = 'https:' + url
                parsed = urlparse(url)
            else:
                return None
        
        # Normalize scheme to lowercase
        scheme = parsed.scheme.lower()
        
        # Only accept http and https
        if scheme not in ('http', 'https'):
            return None
        
        # Normalize domain to lowercase
        netloc = parsed.netloc.lower()
        
        # Remove default ports
        if netloc.endswith(':80') and scheme == 'http':
            netloc = netloc[:-3]
        elif netloc.endswith(':443') and scheme == 'https':
            netloc = netloc[:-4]
        
        # Normalize path
        path = parsed.path or '/'
        path = self._normalize_path(path)
        
        # Handle query parameters
        if self.remove_tracking and parsed.query:
            params = parse_qs(parsed.query)
            # Remove tracking parameters
            params = {k: v for k, v in params.items() if k not in self.TRACKING_PARAMS}
            query = urlencode(params, doseq=True)
        else:
            query = parsed.query
        
        # Handle fragment
        fragment = ''
        if not self.remove_fragments or (parsed.fragment and 
                                         any(parsed.fragment.startswith(keep) 
                                             for keep in self.KEEP_FRAGMENTS)):
            fragment = parsed.fragment
        
        # Reconstruct URL
        normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))
        
        # Validate
        if not validators.url(normalized):
            return None
        
        return normalized
    
    def _normalize_path(self, path: str) -> str:
        """Normalize URL path"""
        # Remove consecutive slashes
        path = re.sub(r'/+', '/', path)
        
        # Remove trailing slash for non-root paths
        if len(path) > 1 and path.endswith('/'):
            path = path.rstrip('/')
        
        # Ensure path starts with /
        if not path.startswith('/'):
            path = '/' + path
        
        return path
    
    def get_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return None
    
    def is_same_domain(self, url1: str, url2: str, include_subdomains: bool = True) -> bool:
        """
        Check if two URLs are from the same domain
        
        Args:
            url1: First URL
            url2: Second URL
            include_subdomains: If False, only match exact domains
            
        Returns:
            True if same domain, False otherwise
        """
        domain1 = self.get_domain(url1)
        domain2 = self.get_domain(url2)
        
        if not domain1 or not domain2:
            return False
        
        if include_subdomains:
            # Extract base domain (e.g., example.com from www.example.com)
            base1 = '.'.join(domain1.split('.')[-2:])
            base2 = '.'.join(domain2.split('.')[-2:])
            return base1 == base2
        else:
            return domain1 == domain2
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        return validators.url(url) is True