"""
Structured data extractor for JSON-LD and Schema.org
"""
import json
import logging
from typing import Dict, Optional, List
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class StructuredDataExtractor:
    """
    Extract structured data (JSON-LD, Microdata) from HTML
    """
    
    def extract(self, html: str, url: str) -> Optional[Dict]:
        """
        Extract structured data
        
        Args:
            html: HTML string
            url: Source URL
            
        Returns:
            Dictionary with extracted structured data or None
        """
        if not html:
            return None
            
        try:
            soup = BeautifulSoup(html, 'lxml')
            structured_data = {}
            
            # 1. Extract JSON-LD
            json_ld = self._extract_json_ld(soup)
            if json_ld:
                structured_data['json_ld'] = json_ld
                
            # 2. Extract Meta Tags (OpenGraph, Twitter)
            meta_tags = self._extract_meta_tags(soup)
            if meta_tags:
                structured_data['meta'] = meta_tags
                
            # 3. Map to common fields
            mapped_data = self._map_to_common_fields(structured_data)
            
            if not mapped_data:
                return None
                
            return {
                **mapped_data,
                'raw_structured_data': structured_data,
                'extraction_confidence': 0.9,
                'parser_used': 'structured_data'
            }
            
        except Exception as e:
            logger.debug(f"Structured data extraction failed for {url}: {e}")
            return None
            
    def _extract_json_ld(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract all JSON-LD blocks"""
        results = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    results.extend(data)
                else:
                    results.append(data)
            except Exception:
                continue
        return results
        
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict:
        """Extract OpenGraph and Twitter meta tags"""
        meta = {}
        for tag in soup.find_all('meta'):
            prop = tag.get('property') or tag.get('name')
            content = tag.get('content')
            if prop and content:
                meta[prop] = content
        return meta
        
    def _map_to_common_fields(self, data: Dict) -> Dict:
        """Map heterogeneous structured data to common fields"""
        result = {}
        
        # Try to find title
        result['title'] = self._find_in_data(data, ['title', 'og:title', 'headline', 'name'])
        
        # Try to find author
        result['author'] = self._find_in_data(data, ['author', 'article:author', 'creator'])
        if isinstance(result['author'], dict):
            result['author'] = result['author'].get('name')
            
        # Try to find date
        result['publish_date'] = self._find_in_data(data, ['datePublished', 'article:published_time', 'pubdate'])
        
        # Try to find description
        result['summary'] = self._find_in_data(data, ['description', 'og:description', 'abstract'])
        
        # Clean up
        return {k: v for k, v in result.items() if v}
        
    def _find_in_data(self, data: Dict, keys: List[str]):
        """Helper to find one of the keys in nested structured data"""
        # Search in meta first (often reliable for basic info)
        meta = data.get('meta', {})
        for key in keys:
            if key in meta:
                return meta[key]
                
        # Search in JSON-LD
        for item in data.get('json_ld', []):
            for key in keys:
                if key in item:
                    return item[key]
                    
        return None
