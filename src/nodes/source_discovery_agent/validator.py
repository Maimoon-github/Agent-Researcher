"""
Validator - Phase 3: Source validation and technical checks
"""

from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
import requests
import httpx
import logging
import asyncio
from datetime import datetime
import re


class SourceValidator:
    """Validates sources for technical accessibility and compliance"""
    
    def __init__(
        self,
        timeout: int = 10,
        user_agent: str = "ResearchAgent/1.0",
        logger: Optional[logging.Logger] = None
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self.logger = logger or logging.getLogger(__name__)
    
    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL syntax according to RFC 3986
        
        Args:
            url: The URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic URL pattern
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
                r'localhost|'  # localhost
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE
            )
            
            if not url_pattern.match(url):
                return False, "Invalid URL format"
            
            # Parse URL
            parsed = urlparse(url)
            
            # Check required components
            if not parsed.scheme:
                return False, "Missing URL scheme (http/https)"
            
            if not parsed.netloc:
                return False, "Missing domain/netloc"
            
            # Validate scheme
            if parsed.scheme not in ['http', 'https']:
                return False, f"Unsupported scheme: {parsed.scheme}"
            
            return True, None
            
        except Exception as e:
            return False, f"URL validation error: {str(e)}"
    
    async def check_reachability_async(self, url: str) -> Dict:
        """Asynchronous version of check_reachability"""
        result = {
            'reachable': False,
            'status_code': None,
            'content_type': None,
            'estimated_size_kb': None,
            'response_time_ms': None,
            'error': None
        }
        
        try:
            self.logger.debug(f"Checking reachability (async) of {url}")
            start_time = datetime.now()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.head(
                    url,
                    headers={'User-Agent': self.user_agent},
                    follow_redirects=True
                )
            
            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            result['status_code'] = response.status_code
            result['response_time_ms'] = response_time_ms
            
            if 200 <= response.status_code < 300:
                result['reachable'] = True
                content_type = response.headers.get('Content-Type', '')
                result['content_type'] = content_type.split(';')[0].strip()
                
                content_length = response.headers.get('Content-Length')
                if content_length:
                    try:
                        result['estimated_size_kb'] = int(content_length) // 1024
                    except ValueError:
                        pass
            else:
                result['error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            result['error'] = str(e)
            
        return result

    def check_reachability(self, url: str) -> Dict:
        """
        Check if URL is reachable via HEAD request
        
        Args:
            url: The URL to check
            
        Returns:
            Dictionary with reachability information
        """
        result = {
            'reachable': False,
            'status_code': None,
            'content_type': None,
            'estimated_size_kb': None,
            'response_time_ms': None,
            'error': None
        }
        
        try:
            self.logger.debug(f"Checking reachability of {url}")
            
            start_time = datetime.now()
            
            # Make HEAD request
            response = requests.head(
                url,
                timeout=self.timeout,
                headers={'User-Agent': self.user_agent},
                allow_redirects=True
            )
            
            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            result['status_code'] = response.status_code
            result['response_time_ms'] = response_time_ms
            
            # Check if successful
            if 200 <= response.status_code < 300:
                result['reachable'] = True
                
                # Extract content type
                content_type = response.headers.get('Content-Type', '')
                result['content_type'] = content_type.split(';')[0].strip()
                
                # Estimate size from Content-Length header
                content_length = response.headers.get('Content-Length')
                if content_length:
                    try:
                        result['estimated_size_kb'] = int(content_length) // 1024
                    except ValueError:
                        pass
                
                self.logger.debug(f"URL {url} is reachable (status: {response.status_code})")
            else:
                result['error'] = f"HTTP {response.status_code}"
                self.logger.warning(f"URL {url} returned status {response.status_code}")
            
        except requests.Timeout:
            result['error'] = "Request timeout"
            self.logger.warning(f"Timeout checking {url}")
        except requests.RequestException as e:
            result['error'] = f"Request error: {str(e)}"
            self.logger.warning(f"Request error for {url}: {str(e)}")
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            self.logger.error(f"Unexpected error checking {url}: {str(e)}")
        
        return result
    
    def validate_content_type(self, content_type: Optional[str]) -> Tuple[bool, str]:
        """
        Validate that content type is parseable
        
        Args:
            content_type: The content type to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if not content_type:
            return False, "No content type specified"
        
        # Acceptable content types
        parseable_types = {
            'text/html',
            'text/plain',
            'application/pdf',
            'application/json',
            'application/xml',
            'text/xml',
            'application/xhtml+xml',
        }
        
        # Check if content type is parseable
        for acceptable in parseable_types:
            if content_type.startswith(acceptable):
                return True, f"Valid content type: {content_type}"
        
        # Check if it's likely a document
        if any(doc_type in content_type.lower() for doc_type in ['document', 'text', 'pdf']):
            return True, f"Likely parseable: {content_type}"
        
        return False, f"Unparseable content type: {content_type}"
    
    def validate_source(self, url: str, credibility_threshold: float = 0.7) -> Dict:
        """
        Comprehensive source validation
        
        Args:
            url: The URL to validate
            credibility_threshold: Minimum credibility score required
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'url': url,
            'valid': False,
            'validation_timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': {
                'url_syntax': False,
                'reachability': False,
                'content_type': False,
            },
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        # Step 3.1: URL Syntax Validation
        is_valid_url, url_error = self.validate_url(url)
        validation_result['checks']['url_syntax'] = is_valid_url
        
        if not is_valid_url:
            validation_result['errors'].append(f"URL syntax validation failed: {url_error}")
            return validation_result
        
        # Step 3.2: Network Reachability Check
        reachability = self.check_reachability(url)
        validation_result['checks']['reachability'] = reachability['reachable']
        validation_result['metadata'].update({
            'status_code': reachability['status_code'],
            'content_type': reachability['content_type'],
            'estimated_size_kb': reachability['estimated_size_kb'],
            'response_time_ms': reachability['response_time_ms']
        })
        
        if not reachability['reachable']:
            validation_result['errors'].append(
                f"Reachability check failed: {reachability.get('error', 'Unknown error')}"
            )
            return validation_result
        
        # Step 3.3: Content-Type Verification
        is_valid_content, content_msg = self.validate_content_type(reachability['content_type'])
        validation_result['checks']['content_type'] = is_valid_content
        
        if not is_valid_content:
            validation_result['warnings'].append(content_msg)
        
        # If all checks passed, mark as valid
        if all(validation_result['checks'].values()):
            validation_result['valid'] = True
        
        return validation_result
    
    async def extract_title_async(self, url: str) -> Optional[str]:
        """Asynchronous version of extract_title"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers={'User-Agent': self.user_agent},
                    follow_redirects=True
                )
            
            if response.status_code == 200:
                title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
                if title_match:
                    return title_match.group(1).strip()
            
        except Exception:
            pass
        
        return None

    def extract_title(self, url: str) -> Optional[str]:
        """
        Extract page title from URL
        
        Args:
            url: The URL to extract title from
            
        Returns:
            Page title or None
        """
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={'User-Agent': self.user_agent}
            )
            
            if response.status_code == 200:
                # Simple title extraction (in production, use BeautifulSoup)
                title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
                if title_match:
                    return title_match.group(1).strip()
            
        except Exception as e:
            self.logger.debug(f"Could not extract title from {url}: {str(e)}")
        
        return None
    
    def batch_validate(self, urls: list) -> Dict[str, Dict]:
        """
        Validate multiple URLs
        
        Args:
            urls: List of URLs to validate
            
        Returns:
            Dictionary mapping URLs to validation results
        """
        results = {}
        
        for url in urls:
            results[url] = self.validate_source(url)
        
        return results