"""
Node 3: Local File Loader

Loads and parses local documents in various formats.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from loguru import logger

from .base import BaseNode
from ..core.state import AgentState, SourceType


class FileLoaderNode(BaseNode):
    """
    Loads local files for processing.
    
    Supported formats:
    - PDF
    - DOCX
    - TXT
    - Markdown
    - HTML
    """
    
    node_name = "file_loader"
    max_retries = 2
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".html", ".htm", ".json"}
    
    def validate_input(self, state: AgentState) -> tuple[bool, str]:
        """Check for local file sources."""
        sources = state.get("sources", [])
        local_sources = [s for s in sources if s.get("source_type") == SourceType.LOCAL_FILE.value]
        if not local_sources:
            logger.info("No local file sources to load")
        return True, ""
    
    def process(self, state: AgentState) -> AgentState:
        """Load all local file sources."""
        sources = state.get("sources", [])
        local_sources = [s for s in sources if s.get("source_type") == SourceType.LOCAL_FILE.value]
        
        if not local_sources:
            state["raw_data"] = state.get("raw_data", [])
            return state
        
        logger.info(f"Loading {len(local_sources)} local files")
        
        raw_data = []
        
        for source in local_sources:
            try:
                result = self._load_file(source)
                if result:
                    raw_data.append(result)
            except Exception as e:
                logger.warning(f"Failed to load {source.get('path')}: {e}")
                self.add_warning(state, f"File load failed: {source.get('path')}")
        
        # Store raw data (will be merged with web data by web scraper)
        state["raw_data"] = raw_data
        
        logger.info(f"Successfully loaded {len(raw_data)} files")
        return state
    
    def _load_file(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Load a single file."""
        file_path = source.get("path")
        if not file_path:
            return None
        
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return None
        
        extension = path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file type: {extension}")
            return None
        
        try:
            content = self._extract_content(path, extension)
            
            return {
                "id": str(uuid.uuid4()),
                "source_id": source.get("id"),
                "content": content,
                "content_type": self._get_content_type(extension),
                "path": str(path),
                "extracted_at": datetime.now().isoformat(),
                "metadata": {
                    "filename": path.name,
                    "extension": extension,
                    "size_bytes": path.stat().st_size,
                    "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                },
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {e}")
            return None
    
    def _extract_content(self, path: Path, extension: str) -> str:
        """Extract text content from file based on type."""
        
        if extension in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="ignore")
        
        elif extension == ".pdf":
            return self._extract_pdf(path)
        
        elif extension in {".docx", ".doc"}:
            return self._extract_docx(path)
        
        elif extension in {".html", ".htm"}:
            return self._extract_html(path)
        
        elif extension == ".json":
            import json
            data = json.loads(path.read_text(encoding="utf-8"))
            return json.dumps(data, indent=2)
        
        else:
            # Fallback to plain text
            return path.read_text(encoding="utf-8", errors="ignore")
    
    def _extract_pdf(self, path: Path) -> str:
        """Extract text from PDF."""
        try:
            import pypdf
            
            text_parts = []
            with open(path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            return "\n\n".join(text_parts)
            
        except ImportError:
            logger.warning("pypdf not installed, trying alternative")
            # Fallback
            return f"[PDF content from: {path.name}]"
    
    def _extract_docx(self, path: Path) -> str:
        """Extract text from DOCX."""
        try:
            from docx import Document
            
            doc = Document(path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
            
        except ImportError:
            logger.warning("python-docx not installed")
            return f"[DOCX content from: {path.name}]"
    
    def _extract_html(self, path: Path) -> str:
        """Extract text from HTML file."""
        from bs4 import BeautifulSoup
        
        html = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove scripts and styles
        for tag in soup(["script", "style"]):
            tag.decompose()
        
        return soup.get_text(separator="\n", strip=True)
    
    def _get_content_type(self, extension: str) -> str:
        """Get MIME type for extension."""
        mime_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".html": "text/html",
            ".htm": "text/html",
            ".json": "application/json",
        }
        return mime_types.get(extension, "text/plain")
