"""
Web Searcher - Phase 2.5: Real-time search engine and API integration
"""

from typing import List, Dict, Optional
import requests
import httpx
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote_plus
import asyncio


class WebSearcher:
    """Performs actual web searches and extracts relevant links from open APIs"""
    
    def __init__(
        self,
        timeout: int = 15,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        logger: Optional[logging.Logger] = None
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self.logger = logger or logging.getLogger(__name__)
        self.headers = {'User-Agent': self.user_agent}
        
    async def search_async(self, query: str, max_results: int = 100) -> List[Dict]:
        """Asynchronous version of search"""
        self.logger.info(f"Performing live search (async) for: {query}")
        
        # Parallelize the different search engines
        tasks = [
            self._search_wikipedia_async(query, max_results=max_results // 2),
            self._search_arxiv_async(query, max_results=max_results // 2),
            self._search_ddg_async(query, max_results=max_results)
        ]
        
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for res in search_results:
            if isinstance(res, list):
                results.extend(res)
                
        self.logger.info(f"Total live sources extracted (async): {len(results)}")
        return results[:max_results]

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Perform a multi-source search using open APIs (Wikipedia, Arxiv).
        
        Args:
            query: The search query
            max_results: Maximum number of links to return
            
        Returns:
            List of source dictionaries with 'url', 'title', and 'snippet'
        """
        self.logger.info(f"Performing live search for: {query}")
        
        results = []
        
        # 1. Search Wikipedia (Web)
        try:
            wiki_results = self._search_wikipedia(query, max_results=max_results // 2)
            results.extend(wiki_results)
        except Exception as e:
            self.logger.debug(f"Wikipedia search failed: {e}")
            
        # 2. Search Arxiv (Academic)
        try:
            arxiv_results = self._search_arxiv(query, max_results=max_results // 2)
            results.extend(arxiv_results)
        except Exception as e:
            self.logger.debug(f"Arxiv search failed: {e}")
            
        # 3. Best effort DuckDuckGo (Global Web)
        if len(results) < max_results:
            try:
                ddg_results = self._search_ddg(query, max_results=max_results - len(results))
                results.extend(ddg_results)
            except Exception as e:
                self.logger.debug(f"DuckDuckGo search failed: {e}")
                
        self.logger.info(f"Total live sources extracted: {len(results)}")
        return results[:max_results]

    async def _search_wikipedia_async(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search Wikipedia API asynchronously"""
        results = []
        api_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote_plus(query)}&format=json"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(api_url, headers=self.headers)
                
            if response.status_code == 200:
                data = response.json()
                for item in data.get('query', {}).get('search', []):
                    title = item.get('title')
                    page_url = f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
                    snippet = BeautifulSoup(item.get('snippet', ''), 'html.parser').get_text()
                    
                    results.append({
                        'url': page_url,
                        'title': f"{title} (Wikipedia)",
                        'snippet': snippet,
                        'source_type': 'web',
                        'generation_method': 'wikipedia_api'
                    })
                    if len(results) >= max_results:
                        break
        except Exception as e:
            self.logger.debug(f"Wikipedia async search failed: {e}")
            
        return results

    def _search_wikipedia(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search Wikipedia API"""
        results = []
        api_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote_plus(query)}&format=json"
        
        response = requests.get(api_url, headers=self.headers, timeout=self.timeout)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('query', {}).get('search', []):
                title = item.get('title')
                page_url = f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
                snippet = BeautifulSoup(item.get('snippet', ''), 'html.parser').get_text()
                
                results.append({
                    'url': page_url,
                    'title': f"{title} (Wikipedia)",
                    'snippet': snippet,
                    'source_type': 'web',
                    'generation_method': 'wikipedia_api'
                })
                if len(results) >= max_results:
                    break
        return results

    async def _search_arxiv_async(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search Arxiv API asynchronously"""
        results = []
        api_url = f"http://export.arxiv.org/api/query?search_query=all:{quote_plus(query)}&max_results={max_results}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(api_url, headers=self.headers)
                
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                entries = soup.find_all('entry')
                for entry in entries:
                    title = entry.find('title').get_text(strip=True)
                    url = entry.find('id').get_text(strip=True)
                    summary = entry.find('summary').get_text(strip=True)
                    
                    results.append({
                        'url': url,
                        'title': f"{title} (Arxiv)",
                        'snippet': summary[:200] + "...",
                        'source_type': 'academic',
                        'generation_method': 'arxiv_api'
                    })
        except Exception as e:
            self.logger.debug(f"Arxiv async search failed: {e}")
            
        return results

    def _search_arxiv(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search Arxiv API"""
        results = []
        api_url = f"http://export.arxiv.org/api/query?search_query=all:{quote_plus(query)}&max_results={max_results}"
        
        response = requests.get(api_url, headers=self.headers, timeout=self.timeout)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'xml') # Use xml parser for Arxiv atom feed
            entries = soup.find_all('entry')
            for entry in entries:
                title = entry.find('title').get_text(strip=True)
                url = entry.find('id').get_text(strip=True)
                summary = entry.find('summary').get_text(strip=True)
                
                results.append({
                    'url': url,
                    'title': f"{title} (Arxiv)",
                    'snippet': summary[:200] + "...",
                    'source_type': 'academic',
                    'generation_method': 'arxiv_api'
                })
        return results

    async def _search_ddg_async(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search DuckDuckGo asynchronously"""
        results = []
        search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(search_url, headers=self.headers, follow_redirects=True)
                
            if response.status_code == 200:
                # Same parsing logic
                soup = BeautifulSoup(response.text, 'html.parser')
                result_divs = soup.select('.result')
                for div in result_divs:
                    title_elem = div.select_one('.result__a')
                    if title_elem:
                        results.append({
                            'url': title_elem.get('href'),
                            'title': title_elem.get_text(strip=True),
                            'snippet': div.select_one('.result__snippet').get_text(strip=True) if div.select_one('.result__snippet') else "",
                            'source_type': 'web',
                            'generation_method': 'ddg_search'
                        })
                        if len(results) >= max_results:
                            break
        except Exception:
            pass
        return results

    def _search_ddg(self, query: str, max_results: int = 5) -> List[Dict]:
        """Best effort DuckDuckGo search"""
        # (This is the original logic, keeping it as fallback)
        results = []
        try:
            search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            response = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                result_divs = soup.select('.result')
                for div in result_divs:
                    title_elem = div.select_one('.result__a')
                    if title_elem:
                        url = title_elem.get('href')
                        results.append({
                            'url': url,
                            'title': title_elem.get_text(strip=True),
                            'snippet': div.select_one('.result__snippet').get_text(strip=True) if div.select_one('.result__snippet') else "",
                            'source_type': 'web',
                            'generation_method': 'ddg_search'
                        })
                        if len(results) >= max_results:
                            break
        except Exception:
            pass
        return results
