import scrapy
from scrapy_playwright.page import PageMethod
from typing import Dict, List, Optional
import time

class DynamicSpider(scrapy.Spider):
    """
    Playwright-enabled spider for dynamic JavaScript content
    """
    name = "dynamic_spider"
    
    def __init__(self, *args, **kwargs):
        super(DynamicSpider, self).__init__(*args, **kwargs)
        self.urls = kwargs.get('urls', [])
        
    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                    'original_url': url
                }
            )
            
    def parse(self, response):
        """Parse the response and return extracted data"""
        item = {
            'source_url': response.meta.get('original_url'),
            'final_url': response.url,
            'http_status': response.status,
            'content_type': response.headers.get('Content-Type', b'').decode('utf-8'),
            'raw_html': response.text,
            'download_timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'javascript_rendered': True
        }
        yield item
