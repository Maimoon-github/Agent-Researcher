"""
Content validation pipeline
"""
import logging
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)


class ValidationPipeline:
    """
    Validates extracted content against quality requirements
    """
    
    def __init__(
        self,
        min_content_length: int = 100,
        max_content_length: int = 100000,
        require_title: bool = False,
        language_filter: Optional[List[str]] = None
    ):
        self.min_content_length = min_content_length
        self.max_content_length = max_content_length
        self.require_title = require_title
        self.language_filter = language_filter or []
    
    def validate(self, content: Dict) -> tuple[bool, List[str]]:
        """
        Validate extracted content
        
        Args:
            content: Extracted content dictionary
            
        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []
        
        # Check content length
        text = content.get('text', '')
        text_length = len(text)
        
        if text_length < self.min_content_length:
            errors.append(f"Content too short: {text_length} < {self.min_content_length}")
        
        if text_length > self.max_content_length:
            errors.append(f"Content too long: {text_length} > {self.max_content_length}")
        
        # Check for title if required
        if self.require_title and not content.get('title'):
            errors.append("Title is required but not found")
        
        # Check language filter
        if self.language_filter:
            detected_lang = content.get('metadata', {}).get('language_detected')
            if detected_lang and detected_lang not in self.language_filter:
                errors.append(f"Language {detected_lang} not in filter: {self.language_filter}")
        
        # Check for gibberish (very high spam score)
        spam_score = content.get('metadata', {}).get('spam_score', 0.0)
        if spam_score > 0.8:
            errors.append(f"Content appears to be spam/gibberish: score={spam_score}")
        
        # Check extraction confidence
        confidence = content.get('extraction_confidence', 1.0)
        if confidence < 0.3:
            errors.append(f"Low extraction confidence: {confidence}")
        
        is_valid = len(errors) == 0
        
        if not is_valid:
            logger.debug(f"Validation failed: {', '.join(errors)}")
        
        return is_valid, errors
    
    def filter_valid_content(self, content_list: List[Dict]) -> tuple[List[Dict], List[Dict]]:
        """
        Filter content list into valid and invalid items
        
        Args:
            content_list: List of content dictionaries
            
        Returns:
            Tuple of (valid_content, invalid_content)
        """
        valid = []
        invalid = []
        
        for content in content_list:
            is_valid, errors = self.validate(content)
            if is_valid:
                valid.append(content)
            else:
                content['validation_errors'] = errors
                invalid.append(content)
        
        logger.info(f"Validation results: {len(valid)} valid, {len(invalid)} invalid")
        
        return valid, invalid