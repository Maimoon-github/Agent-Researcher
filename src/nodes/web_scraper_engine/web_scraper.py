"""
Node 2: Web Scraper Engine

Extracts data from web sources with rate limiting and error handling.
"""

import time
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from loguru import logger
import httpx
from bs4 import BeautifulSoup

from ..base import BaseNode
from ...core.state import AgentState, SourceType


class WebScraperNode(BaseNode):
    """
    Scrapes web sources for content.
    
    Features:
    - Rate limiting
    - Concurrent requests with semaphore
    - Content extraction with BeautifulSoup
    - Error handling per source
    """
    
    node_name = "web_scraper"
    max_retries = 3
    
    def validate_input(self, state: AgentState) -> tuple[bool, str]:
        """Validate that we have sources to scrape."""
        sources = state.get("sources", [])
        web_sources = [s for s in sources if s.get("source_type") == SourceType.WEB.value]
        if not web_sources:
            # Not an error - might only have local files
            logger.info("No web sources to scrape")
        return True, ""
    
    def process(self, state: AgentState) -> AgentState:
        """Scrape all web sources."""
        sources = state.get("sources", [])
        web_sources = [
            s for s in sources 
            if s.get("source_type") == SourceType.WEB.value and s.get("robots_allowed", True)
        ]
        
        if not web_sources:
            state["raw_data"] = state.get("raw_data", [])
            return state
        
        logger.info(f"Scraping {len(web_sources)} web sources")
        
        raw_data = []
        
        # Process sources with rate limiting
        for source in web_sources:
            try:
                result = self._scrape_url(source)
                if result:
                    raw_data.append(result)
                
                # Rate limiting
                time.sleep(self.config.scraping.rate_limit_delay)
                
            except Exception as e:
                logger.warning(f"Failed to scrape {source.get('url')}: {e}")
                self.add_warning(state, f"Scrape failed for {source.get('url')}: {e}")
        
        # Merge with existing raw_data (from file loader)
        existing_data = state.get("raw_data", [])
        state["raw_data"] = existing_data + raw_data
        
        # Update metrics
        if "metrics" in state:
            state["metrics"]["sources_processed"] = state["metrics"].get("sources_processed", 0) + len(raw_data)
        
        logger.info(f"Successfully scraped {len(raw_data)} sources")
        return state
    
    def _scrape_url(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Scrape a single URL."""
        url = source.get("url")
        if not url:
            return None
        
        try:
            with httpx.Client(
                timeout=self.config.scraping.timeout,
                headers={"User-Agent": self.config.scraping.user_agent},
                follow_redirects=True,
            ) as client:
                response = client.get(url)
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "")
                
                if "text/html" in content_type:
                    content = self._extract_html_content(response.text, url)
                else:
                    content = response.text
                
                return {
                    "id": str(uuid.uuid4()),
                    "source_id": source.get("id"),
                    "content": content,
                    "content_type": content_type,
                    "url": url,
                    "extracted_at": datetime.now().isoformat(),
                    "metadata": {
                        "status_code": response.status_code,
                        "content_length": len(content),
                        "headers": dict(response.headers),
                    },
                }
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout scraping {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} for {url}")
            return None
        except Exception as e:
            logger.warning(f"Error scraping {url}: {e}")
            return None
    
    def _extract_html_content(self, html: str, url: str) -> str:
        """Extract meaningful content from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove unwanted elements
        for tag in soup(["script", "style", "nav", "footer", "aside", "iframe", "noscript"]):
            tag.decompose()
        
        # Try to find main content
        main_content = None
        
        # Look for common content containers
        for selector in ["article", "main", '[role="main"]', ".content", "#content", ".post"]:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.body if soup.body else soup
        
        # Extract text
        text = main_content.get_text(separator="\n", strip=True)
        
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
        
        # Add title if available
        title = soup.title.string if soup.title else ""
        if title:
            text = f"# {title}\n\n{text}"
        
        return text
