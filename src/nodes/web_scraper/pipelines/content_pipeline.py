"""
Content processing pipeline
"""
import logging
from typing import Dict, Optional, List
import langdetect
import textstat
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from ..utils import ContentCleaner


logger = logging.getLogger(__name__)


class ContentPipeline:
    """
    Processes and enhances extracted content
    """
    
    def __init__(self, preserve_structure: bool = True):
        self.content_cleaner = ContentCleaner(preserve_structure=preserve_structure)
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    def process(self, extracted_content: Dict) -> Dict:
        """
        Process extracted content
        
        Args:
            extracted_content: Raw extracted content
            
        Returns:
            Processed content with enhancements
        """
        try:
            # Clean text
            if 'text' in extracted_content:
                extracted_content['text'] = self.content_cleaner.clean_text(
                    extracted_content['text']
                )
            
            # Add metadata enhancements
            metadata = self._enhance_metadata(extracted_content)
            extracted_content['metadata'] = metadata
            
            # Add quality assessment
            quality = self._assess_quality(extracted_content)
            extracted_content['quality_metrics'] = quality
            
            return extracted_content
            
        except Exception as e:
            logger.error(f"Content processing error: {e}")
            return extracted_content
    
    def _enhance_metadata(self, content: Dict) -> Dict:
        """Add metadata enhancements"""
        metadata = content.get('metadata', {})
        text = content.get('text', '')
        
        if not text:
            return metadata
        
        try:
            # Language detection
            metadata['language_detected'] = self._detect_language(text)
            
            # Readability scoring
            metadata['readability_score'] = self._calculate_readability(text)
            
            # Spam/quality detection
            metadata['spam_score'] = self._detect_spam(text)
            
            # Sentiment analysis
            metadata['sentiment'] = self._analyze_sentiment(text)
            
        except Exception as e:
            logger.debug(f"Metadata enhancement error: {e}")
        
        return metadata
    
    def _detect_language(self, text: str) -> str:
        """Detect text language"""
        try:
            if len(text) < 50:
                return "unknown"
            lang = langdetect.detect(text)
            return lang
        except Exception:
            return "unknown"
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (0.0 to 1.0)"""
        try:
            if len(text) < 100:
                return 0.0
            
            # Flesch Reading Ease (0-100, higher = easier)
            flesch_score = textstat.flesch_reading_ease(text)
            
            # Normalize to 0.0-1.0
            # 90-100: Very Easy (0.9-1.0)
            # 60-90: Easy (0.6-0.9)
            # 30-60: Fairly Difficult (0.3-0.6)
            # 0-30: Very Difficult (0.0-0.3)
            normalized = min(1.0, max(0.0, flesch_score / 100))
            
            return round(normalized, 2)
            
        except Exception:
            return 0.5  # Default to medium
    
    def _detect_spam(self, text: str) -> float:
        """
        Detect spam/low quality content (0.0 = not spam, 1.0 = definitely spam)
        
        Simple heuristics:
        - Too many caps
        - Too many exclamation marks
        - Excessive punctuation
        - Very short sentences
        """
        if not text or len(text) < 50:
            return 0.5
        
        score = 0.0
        
        # Check for excessive caps
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
        if caps_ratio > 0.3:
            score += 0.3
        
        # Check for excessive exclamation marks
        exclamation_ratio = text.count('!') / max(1, len(text.split()))
        if exclamation_ratio > 0.1:
            score += 0.2
        
        # Check for very short text
        if len(text) < 100:
            score += 0.2
        
        # Check for repeated characters
        repeated = sum(1 for i in range(len(text)-1) if text[i] == text[i+1])
        if repeated / len(text) > 0.1:
            score += 0.3
        
        return min(1.0, score)
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyze text sentiment"""
        try:
            if len(text) < 50:
                return "neutral"
            
            # Get VADER scores
            scores = self.sentiment_analyzer.polarity_scores(text)
            compound = scores['compound']
            
            # Classify
            if compound >= 0.05:
                return "positive"
            elif compound <= -0.05:
                return "negative"
            else:
                return "neutral"
                
        except Exception:
            return "neutral"
    
    def _assess_quality(self, content: Dict) -> Dict:
        """Assess content quality"""
        quality = {
            'has_title': bool(content.get('title')),
            'has_author': bool(content.get('author') or content.get('authors')),
            'has_date': bool(content.get('publish_date')),
            'has_structure': bool(content.get('sections')),
            'text_length': len(content.get('text', '')),
            'word_count': content.get('word_count', 0),
            'overall_quality': 0.0
        }
        
        # Calculate overall quality score
        score = 0.0
        if quality['has_title']:
            score += 0.2
        if quality['has_author']:
            score += 0.1
        if quality['has_date']:
            score += 0.1
        if quality['has_structure']:
            score += 0.2
        if quality['text_length'] > 500:
            score += 0.2
        if quality['word_count'] > 100:
            score += 0.2
        
        quality['overall_quality'] = round(min(1.0, score), 2)
        
        return quality