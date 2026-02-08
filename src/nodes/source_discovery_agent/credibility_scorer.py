"""
Credibility Scorer - Multi-factor credibility assessment system
"""

from typing import Dict, Optional
from urllib.parse import urlparse
import logging
from datetime import datetime
import tldextract


class CredibilityScorer:
    """
    Multi-factor credibility scoring system for sources
    
    Scoring Components:
    - Domain Authority (0-30 points)
    - Content Quality (0-40 points)
    - External Validation (0-30 points)
    
    Total Score: 0.0 - 1.0 (normalized)
    """
    
    # TLD scoring
    TLD_SCORES = {
        '.gov': 30,
        '.edu': 25,
        '.org': 20,
        '.com': 15,
        '.net': 12,
        '.io': 10,
        '.co': 10,
    }
    
    # Known high-authority domains
    HIGH_AUTHORITY_DOMAINS = {
        'wikipedia.org': 0.9,
        'nature.com': 0.95,
        'science.org': 0.95,
        'ieee.org': 0.95,
        'arxiv.org': 0.85,
        'pubmed.ncbi.nlm.nih.gov': 0.95,
        'nasa.gov': 0.95,
        'cdc.gov': 0.95,
        'who.int': 0.95,
        'stackoverflow.com': 0.80,
        'github.com': 0.75,
        'reuters.com': 0.85,
        'apnews.com': 0.85,
        'bbc.com': 0.85,
        'nytimes.com': 0.80,
    }
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        self.logger = logger or logging.getLogger(__name__)
    
    def calculate_score(
        self,
        url: str,
        metadata: Optional[Dict] = None
    ) -> float:
        """
        Calculate comprehensive credibility score for a source
        
        Args:
            url: The URL to score
            metadata: Optional metadata about the source
            
        Returns:
            Credibility score between 0.0 and 1.0
        """
        metadata = metadata or {}
        
        # Calculate component scores
        domain_score = self._calculate_domain_authority(url)
        content_score = self._calculate_content_quality(url, metadata)
        external_score = self._calculate_external_validation(url, metadata)
        
        # Determine if we have significant metadata
        # (Discovery phase usually only has basic technical metadata)
        has_rich_metadata = any(k in metadata for k in ['author', 'publication_date', 'citation_count', 'social_shares'])
        
        if not has_rich_metadata:
            # During discovery, we rely heavily on domain reputation.
            # Technical metadata (like size) can provide a small boost but shouldn't be required.
            domain_norm = domain_score / 30.0
            technical_norm = content_score / 40.0
            
            # Base score is the domain reputation, boost slightly with technical info
            total_score = domain_norm + (technical_norm * 0.1)
        else:
            # Full assessment (post-scraping)
            # Weighted combination (normalized to 0-1)
            total_score = (domain_score + content_score + external_score) / 100.0
        
        # Clamp to valid range
        total_score = max(0.0, min(1.0, total_score))
        
        self.logger.debug(
            f"Credibility score for {url}: {total_score:.2f} "
            f"(domain: {domain_score}, content: {content_score}, external: {external_score})"
        )
        
        return total_score
    
    def _calculate_domain_authority(self, url: str) -> float:
        """
        Calculate domain authority score (0-30 points)
        
        Components:
        - TLD analysis (0-30)
        - Known authority domain (+bonus)
        - SSL certificate (+5)
        """
        score = 0.0
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check if it's a known high-authority domain
            if domain in self.HIGH_AUTHORITY_DOMAINS:
                # Convert 0-1 score to 0-30 scale
                return self.HIGH_AUTHORITY_DOMAINS[domain] * 30
            
            # Extract TLD
            ext = tldextract.extract(url)
            tld = f".{ext.suffix}" if ext.suffix else ''
            
            # TLD scoring
            score += self.TLD_SCORES.get(tld, 8)  # Default score for other TLDs
            
            # SSL certificate bonus
            if parsed.scheme == 'https':
                score += 5
            
            # Domain length (shorter, more established domains tend to be more credible)
            domain_parts = ext.domain
            if domain_parts and len(domain_parts) < 15:
                score += 2
            
        except Exception as e:
            self.logger.warning(f"Error calculating domain authority for {url}: {str(e)}")
        
        return min(score, 30)  # Cap at 30
    
    def _calculate_content_quality(self, url: str, metadata: Dict) -> float:
        """
        Calculate content quality score (0-40 points)
        
        Components:
        - Author identification (+10)
        - Publication date recency (+10)
        - Content length/depth (+10)
        - Readability and structure (+10)
        """
        score = 0.0
        
        try:
            # Author identification
            if metadata.get('author'):
                score += 10
            elif metadata.get('has_byline'):
                score += 5
            
            # Publication date recency
            pub_date = metadata.get('publication_date')
            if pub_date:
                try:
                    if isinstance(pub_date, str):
                        pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    
                    age_days = (datetime.now() - pub_date).days
                    
                    # Score based on recency (newer is better for most content)
                    if age_days < 30:
                        score += 10
                    elif age_days < 180:
                        score += 8
                    elif age_days < 365:
                        score += 6
                    elif age_days < 730:
                        score += 4
                    else:
                        score += 2
                except Exception:
                    pass
            
            # Content depth (estimated by size)
            content_size = metadata.get('estimated_size_kb')
            if content_size is not None:
                if content_size > 100:
                    score += 10
                elif content_size > 50:
                    score += 7
                elif content_size > 20:
                    score += 5
                elif content_size > 0:
                    score += 3
            
            # Structured content indicators
            if metadata.get('has_structured_data'):
                score += 5
            if metadata.get('has_references'):
                score += 5
            
        except Exception as e:
            self.logger.warning(f"Error calculating content quality for {url}: {str(e)}")
        
        return min(score, 40)  # Cap at 40
    
    def _calculate_external_validation(self, url: str, metadata: Dict) -> float:
        """
        Calculate external validation score (0-30 points)
        
        Components:
        - Cross-references with other sources (+10)
        - Social validation (+10)
        - Expert endorsements (+10)
        """
        score = 0.0
        
        try:
            # Cross-referencing
            citation_count = metadata.get('citation_count')
            if citation_count is not None:
                if citation_count > 100:
                    score += 10
                elif citation_count > 50:
                    score += 8
                elif citation_count > 10:
                    score += 5
                elif citation_count > 0:
                    score += 3
            
            # Social validation (quality over quantity)
            social_shares = metadata.get('social_shares')
            if social_shares is not None:
                if social_shares > 1000:
                    score += 10
                elif social_shares > 100:
                    score += 7
                elif social_shares > 10:
                    score += 4
            
            # Expert endorsements or institutional backing
            if metadata.get('institutional_backing'):
                score += 10
            if metadata.get('expert_reviewed'):
                score += 5
            
        except Exception as e:
            self.logger.warning(f"Error calculating external validation for {url}: {str(e)}")
        
        return min(score, 30)  # Cap at 30
    
    def get_score_breakdown(
        self,
        url: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Get detailed breakdown of credibility score
        
        Returns:
            Dictionary with score components and total
        """
        metadata = metadata or {}
        
        domain_score = self._calculate_domain_authority(url)
        content_score = self._calculate_content_quality(url, metadata)
        external_score = self._calculate_external_validation(url, metadata)
        total_score = (domain_score + content_score + external_score) / 100.0
        
        return {
            'url': url,
            'total_score': total_score,
            'components': {
                'domain_authority': domain_score,
                'content_quality': content_score,
                'external_validation': external_score
            },
            'breakdown': {
                'tld': self._get_tld_info(url),
                'ssl': urlparse(url).scheme == 'https',
                'known_authority': urlparse(url).netloc.lower() in self.HIGH_AUTHORITY_DOMAINS,
            }
        }
    
    def _get_tld_info(self, url: str) -> Dict:
        """Get TLD information for a URL"""
        try:
            ext = tldextract.extract(url)
            tld = f".{ext.suffix}" if ext.suffix else ''
            return {
                'tld': tld,
                'domain': ext.domain,
                'score': self.TLD_SCORES.get(tld, 8)
            }
        except Exception:
            return {'tld': 'unknown', 'domain': '', 'score': 0}