"""
Newspaper3k-based content extractor
"""
import logging
from typing import Dict, Optional
from newspaper import Article, Config as NewspaperConfig
from newspaper.article import ArticleException


logger = logging.getLogger(__name__)


class NewspaperExtractor:
    """
    Extract article content using newspaper3k library
    """
    
    def __init__(self, language: str = 'en'):
        self.language = language
        self.config = NewspaperConfig()
        self.config.language = language
        self.config.fetch_images = False  # Don't download images
        self.config.memoize_articles = False
    
    def extract(self, url: str, html: Optional[str] = None) -> Optional[Dict]:
        """
        Extract article content
        
        Args:
            url: Article URL
            html: Pre-fetched HTML (optional)
            
        Returns:
            Dictionary with extracted content or None
        """
        try:
            article = Article(url, config=self.config)
            
            if html:
                article.set_html(html)
                article.parse()
            else:
                article.download()
                article.parse()
            
            # Try to get NLP features
            try:
                article.nlp()
            except Exception as e:
                logger.debug(f"NLP processing failed: {e}")
            
            # Extract data
            result = {
                'title': article.title or None,
                'text': article.text or None,
                'authors': article.authors if article.authors else [],
                'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                'top_image': article.top_image or None,
                'images': list(article.images) if article.images else [],
                'videos': list(article.movies) if article.movies else [],
                'keywords': article.keywords if hasattr(article, 'keywords') else [],
                'summary': article.summary if hasattr(article, 'summary') else None,
                'meta_description': article.meta_description or None,
                'meta_keywords': article.meta_keywords or None,
                'canonical_link': article.canonical_link or None,
                'extraction_confidence': self._calculate_confidence(article)
            }
            
            # Validate extraction
            if not result['text'] or len(result['text']) < 100:
                return None
            
            return result
            
        except ArticleException as e:
            logger.debug(f"Newspaper extraction failed for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error extracting {url}: {e}")
            return None
    
    def _calculate_confidence(self, article: Article) -> float:
        """Calculate confidence score for extraction"""
        score = 0.0
        
        # Has title
        if article.title:
            score += 0.2
        
        # Has substantial text
        if article.text and len(article.text) > 500:
            score += 0.3
        elif article.text:
            score += 0.15
        
        # Has author
        if article.authors:
            score += 0.1
        
        # Has publish date
        if article.publish_date:
            score += 0.1
        
        # Has images
        if article.images:
            score += 0.1
        
        # Has summary/keywords
        if hasattr(article, 'summary') and article.summary:
            score += 0.1
        
        # Has metadata
        if article.meta_description or article.meta_keywords:
            score += 0.1
        
        return min(1.0, score)