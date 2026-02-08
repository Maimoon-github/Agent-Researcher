"""
PDF content extractor
"""
import logging
from typing import Dict, Optional
import io
from pypdf import PdfReader


logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extract text content from PDF files
    """
    
    def __init__(self, max_pages: Optional[int] = None):
        self.max_pages = max_pages
    
    def extract(self, pdf_data: bytes, url: str) -> Optional[Dict]:
        """
        Extract text from PDF
        
        Args:
            pdf_data: PDF file bytes
            url: Source URL
            
        Returns:
            Dictionary with extracted content or None
        """
        if not pdf_data:
            return None
        
        try:
            # Create PDF reader
            pdf_file = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_file)
            
            # Extract metadata
            metadata = self._extract_metadata(reader)
            
            # Extract text from pages
            pages_to_read = min(len(reader.pages), self.max_pages) if self.max_pages else len(reader.pages)
            
            text_parts = []
            for page_num in range(pages_to_read):
                try:
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num}: {e}")
                    continue
            
            full_text = '\n\n'.join(text_parts)
            
            # Validate extraction
            if not full_text or len(full_text) < 100:
                return None
            
            result = {
                'title': metadata.get('title') or self._extract_title_from_text(full_text),
                'author': metadata.get('author'),
                'text': full_text,
                'page_count': len(reader.pages),
                'pages_extracted': pages_to_read,
                'metadata': metadata,
                'word_count': len(full_text.split()),
                'extraction_confidence': self._calculate_confidence(full_text, metadata)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"PDF extraction failed for {url}: {e}")
            return None
    
    def _extract_metadata(self, reader: PdfReader) -> Dict:
        """Extract PDF metadata"""
        metadata = {}
        
        try:
            if reader.metadata:
                metadata = {
                    'title': reader.metadata.get('/Title'),
                    'author': reader.metadata.get('/Author'),
                    'subject': reader.metadata.get('/Subject'),
                    'creator': reader.metadata.get('/Creator'),
                    'producer': reader.metadata.get('/Producer'),
                    'creation_date': reader.metadata.get('/CreationDate'),
                    'modification_date': reader.metadata.get('/ModDate')
                }
                
                # Clean up values
                metadata = {k: str(v) if v else None for k, v in metadata.items()}
        
        except Exception as e:
            logger.debug(f"Could not extract PDF metadata: {e}")
        
        return metadata
    
    def _extract_title_from_text(self, text: str) -> Optional[str]:
        """Try to extract title from first few lines"""
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                return line
        return None
    
    def _calculate_confidence(self, text: str, metadata: Dict) -> float:
        """Calculate extraction confidence"""
        score = 0.3  # Base score for PDF
        
        # Has substantial text
        if len(text) > 1000:
            score += 0.3
        elif len(text) > 500:
            score += 0.2
        
        # Has metadata
        if metadata.get('title'):
            score += 0.1
        if metadata.get('author'):
            score += 0.1
        
        # Check text quality (not too many extraction errors)
        error_indicators = text.count('�')  # Unicode replacement character
        if error_indicators < 10:
            score += 0.2
        
        return min(1.0, score)
    
    def extract_from_file(self, file_path: str) -> Optional[Dict]:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with extracted content or None
        """
        try:
            with open(file_path, 'rb') as f:
                pdf_data = f.read()
            return self.extract(pdf_data, file_path)
        except Exception as e:
            logger.error(f"Failed to read PDF file {file_path}: {e}")
            return None