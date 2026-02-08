"""
Readability-based content extractor
"""
import logging
from typing import Dict, Optional
from readability import Document
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class ReadabilityExtractor:
    """
    Extract main content using Mozilla's Readability algorithm
    """
    
    def __init__(self):
        self.min_text_length = 100
    
    def extract(self, html: str, url: str) -> Optional[Dict]:
        """
        Extract content using readability
        
        Args:
            html: HTML string
            url: Source URL
            
        Returns:
            Dictionary with extracted content or None
        """
        if not html:
            return None
        
        try:
            doc = Document(html)
            
            # Extract title
            title = doc.title()
            
            # Extract main content
            content_html = doc.summary()
            
            # Convert to text
            soup = BeautifulSoup(content_html, 'lxml')
            text = soup.get_text(separator='\n', strip=True)
            
            # Validate extraction
            if not text or len(text) < self.min_text_length:
                return None
            
            # Extract structure
            sections = self._extract_sections(soup)
            
            result = {
                'title': title or None,
                'text': text,
                'html': content_html,
                'sections': sections,
                'word_count': len(text.split()),
                'extraction_confidence': self._calculate_confidence(text, sections)
            }
            
            return result
            
        except Exception as e:
            logger.debug(f"Readability extraction failed for {url}: {e}")
            return None
    
    def _extract_sections(self, soup: BeautifulSoup) -> list:
        """Extract content sections with headings"""
        sections = []
        current_section = {'heading': None, 'content': [], 'word_count': 0}
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol']):
            if element.name.startswith('h'):
                # Save previous section if it has content
                if current_section['content']:
                    content_text = '\n'.join(current_section['content'])
                    current_section['content'] = content_text
                    current_section['word_count'] = len(content_text.split())
                    sections.append(current_section.copy())
                
                # Start new section
                current_section = {
                    'heading': element.get_text(strip=True),
                    'content': [],
                    'word_count': 0
                }
            else:
                # Add content to current section
                text = element.get_text(strip=True)
                if text:
                    current_section['content'].append(text)
        
        # Add final section
        if current_section['content']:
            content_text = '\n'.join(current_section['content'])
            current_section['content'] = content_text
            current_section['word_count'] = len(content_text.split())
            sections.append(current_section)
        
        return sections
    
    def _calculate_confidence(self, text: str, sections: list) -> float:
        """Calculate extraction confidence"""
        score = 0.0
        
        # Length-based confidence
        text_length = len(text)
        if text_length > 2000:
            score += 0.4
        elif text_length > 1000:
            score += 0.3
        elif text_length > 500:
            score += 0.2
        else:
            score += 0.1
        
        # Structure-based confidence
        if sections:
            score += 0.2
            if len(sections) > 3:
                score += 0.1
        
        # Check for reasonable paragraph structure
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 3:
            score += 0.1
            avg_para_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            if 20 < avg_para_length < 200:  # Reasonable paragraph length
                score += 0.2
        
        return min(1.0, score)