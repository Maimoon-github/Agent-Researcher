 
"""
Content cleaning and normalization utilities
"""
import re
import ftfy
from typing import Optional
from bs4 import BeautifulSoup, Comment


class ContentCleaner:
    """
    Cleans and normalizes extracted content
    """
    
    # Tags to completely remove
    REMOVE_TAGS = [
        'script', 'style', 'noscript', 'iframe', 'embed', 'object',
        'applet', 'link', 'meta'
    ]
    
    # Tags to unwrap (keep content but remove tag)
    UNWRAP_TAGS = ['font', 'center', 'marquee']
    
    def __init__(self, preserve_structure: bool = True):
        self.preserve_structure = preserve_structure
    
    def clean_html(self, html: str) -> str:
        """
        Clean HTML content
        
        Args:
            html: Raw HTML string
            
        Returns:
            Cleaned HTML string
        """
        if not html:
            return ""
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove unwanted tags
        for tag in self.REMOVE_TAGS:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Unwrap certain tags
        for tag in self.UNWRAP_TAGS:
            for element in soup.find_all(tag):
                element.unwrap()
        
        # Remove empty tags
        for element in soup.find_all():
            if len(element.get_text(strip=True)) == 0 and not element.name in ['br', 'hr', 'img']:
                element.decompose()
        
        return str(soup)
    
    def html_to_text(self, html: str, preserve_links: bool = False) -> str:
        """
        Convert HTML to clean text
        
        Args:
            html: HTML string
            preserve_links: Keep link URLs in text
            
        Returns:
            Clean text string
        """
        if not html:
            return ""
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove unwanted elements
        for tag in self.REMOVE_TAGS:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Handle links
        if preserve_links:
            for link in soup.find_all('a', href=True):
                link.string = f"{link.get_text()} ({link['href']})"
        
        # Convert to text
        text = soup.get_text(separator='\n' if self.preserve_structure else ' ')
        
        # Clean up the text
        text = self.clean_text(text)
        
        return text
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
        
        # Fix encoding issues
        text = ftfy.fix_text(text)
        
        # Normalize unicode
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove zero-width characters
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
        
        # Remove excessive whitespace
        if self.preserve_structure:
            # Keep paragraph breaks but clean up lines
            lines = text.split('\n')
            lines = [' '.join(line.split()) for line in lines]
            # Remove empty lines
            lines = [line for line in lines if line.strip()]
            text = '\n\n'.join(lines)
        else:
            # Collapse all whitespace
            text = ' '.join(text.split())
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_main_content(self, html: str) -> str:
        """
        Extract main content from HTML using heuristics
        
        Args:
            html: HTML string
            
        Returns:
            Main content as text
        """
        if not html:
            return ""
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove unwanted elements
        for tag in self.REMOVE_TAGS:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Try to find main content area
        main_content = None
        
        # Look for common main content tags/classes
        for selector in [
            'main', 'article', '[role="main"]',
            '.main-content', '.article-content', '.post-content',
            '#main-content', '#article-content', '#content'
        ]:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If not found, use body
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Convert to text
        text = self.html_to_text(str(main_content))
        
        return text
    
    def remove_boilerplate(self, text: str) -> str:
        """
        Remove boilerplate text (footer, navigation, etc.)
        
        Args:
            text: Text string
            
        Returns:
            Text with boilerplate removed
        """
        # Common boilerplate patterns
        boilerplate_patterns = [
            r'©\s*\d{4}.*?All rights reserved',
            r'Privacy Policy.*?Terms of Service',
            r'Follow us on.*?(?:Twitter|Facebook|Instagram)',
            r'Subscribe to our newsletter',
        ]
        
        for pattern in boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text.strip()
    
    def truncate(self, text: str, max_length: int, suffix: str = "...") -> str:
        """
        Truncate text to maximum length
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to add when truncated
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)].rsplit(' ', 1)[0] + suffix