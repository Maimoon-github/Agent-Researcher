"""
Custom extractor with CSS/XPath selector support
"""
import logging
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
import re


logger = logging.getLogger(__name__)


class CustomExtractor:
    """
    Extract content using custom CSS/XPath selectors or heuristics
    """
    
    def __init__(self, extraction_patterns: Optional[Dict] = None):
        self.extraction_patterns = extraction_patterns or {}
    
    def extract(self, html: str, url: str) -> Optional[Dict]:
        """
        Extract content using custom patterns or fallback heuristics
        
        Args:
            html: HTML string
            url: Source URL
            
        Returns:
            Dictionary with extracted content or None
        """
        if not html:
            return None
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Try custom patterns first
            if self.extraction_patterns:
                result = self._extract_with_patterns(soup, url)
                if result:
                    return result
            
            # Fallback to heuristics
            return self._extract_with_heuristics(soup, url)
            
        except Exception as e:
            logger.error(f"Custom extraction failed for {url}: {e}")
            return None
    
    def _extract_with_patterns(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Extract using provided CSS selectors"""
        try:
            result = {}
            
            # Extract each field using patterns
            for field, selector in self.extraction_patterns.items():
                element = soup.select_one(selector)
                if element:
                    if field in ['title', 'author', 'date_published']:
                        result[field] = element.get_text(strip=True)
                    elif field == 'main_content':
                        result['text'] = element.get_text(separator='\n', strip=True)
                        result['html'] = str(element)
                    elif field == 'categories':
                        result[field] = [e.get_text(strip=True) for e in soup.select(selector)]
            
            # Validate
            if result.get('text') and len(result['text']) > 100:
                result['extraction_confidence'] = 0.8
                return result
            
            return None
            
        except Exception as e:
            logger.debug(f"Pattern extraction failed: {e}")
            return None
    
    def _extract_with_heuristics(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Extract using content heuristics"""
        try:
            # Remove unwanted elements
            for tag in ['script', 'style', 'nav', 'header', 'footer', 'aside']:
                for element in soup.find_all(tag):
                    element.decompose()
            
            # Try to find main content
            main_element = self._find_main_content(soup)
            if not main_element:
                return None
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract text from main element
            text = main_element.get_text(separator='\n', strip=True)
            
            # Validate
            if not text or len(text) < 100:
                return None
            
            # Extract sections
            sections = self._extract_sections_from_element(main_element)
            
            result = {
                'title': title,
                'text': text,
                'html': str(main_element),
                'sections': sections,
                'word_count': len(text.split()),
                'extraction_confidence': 0.5  # Lower confidence for heuristic extraction
            }
            
            return result
            
        except Exception as e:
            logger.debug(f"Heuristic extraction failed: {e}")
            return None
    
    def _find_main_content(self, soup: BeautifulSoup):
        """Find main content element using heuristics"""
        # Try semantic HTML5 tags
        for tag in ['article', 'main', '[role="main"]']:
            element = soup.select_one(tag)
            if element:
                return element
        
        # Try common class names/IDs
        for selector in ['.main-content', '.article-content', '.post-content',
                        '#main-content', '#article-content', '#content']:
            element = soup.select_one(selector)
            if element:
                return element
        
        # Find element with most text
        candidates = []
        for element in soup.find_all(['div', 'section']):
            text_length = len(element.get_text(strip=True))
            if text_length > 200:
                candidates.append((element, text_length))
        
        if candidates:
            # Return element with most text
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        
        # Last resort: use body
        return soup.find('body')
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title"""
        # Try <title> tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        # Try h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        # Try og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content']
        
        return None
    
    def _extract_sections_from_element(self, element) -> List[Dict]:
        """Extract sections from an element"""
        sections = []
        current_section = {'heading': None, 'content': [], 'word_count': 0}
        
        for child in element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
            if child.name.startswith('h'):
                # Save previous section
                if current_section['content']:
                    content_text = '\n'.join(current_section['content'])
                    current_section['content'] = content_text
                    current_section['word_count'] = len(content_text.split())
                    sections.append(current_section.copy())
                
                # Start new section
                current_section = {
                    'heading': child.get_text(strip=True),
                    'content': [],
                    'word_count': 0
                }
            elif child.name == 'p':
                text = child.get_text(strip=True)
                if text:
                    current_section['content'].append(text)
        
        # Add final section
        if current_section['content']:
            content_text = '\n'.join(current_section['content'])
            current_section['content'] = content_text
            current_section['word_count'] = len(content_text.split())
            sections.append(current_section)
        
        return sections