import scrapy
from scrapy.http import HtmlResponse
from typing import Dict, List, Optional
import time

class StaticSpider(scrapy.Spider):
    """
    Traditional Scrapy spider for static HTML content
    """
    name = "static_spider"
    
    def __init__(self, *args, **kwargs):
        super(StaticSpider, self).__init__(*args, **kwargs)
        self.urls = kwargs.get('urls', [])
        self.extraction_patterns = kwargs.get('extraction_patterns', {})
        
    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'original_url': url}
            )
            
    def parse(self, response: HtmlResponse):
        """Parse the response and return extracted data"""
        item = {
            'source_url': response.meta.get('original_url'),
            'final_url': response.url,
            'http_status': response.status,
            'content_type': response.headers.get('Content-Type', b'').decode('utf-8'),
            'raw_html': response.text,
            'download_timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        yield item
