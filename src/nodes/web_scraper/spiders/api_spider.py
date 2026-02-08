import scrapy
import json
import time

class APISpider(scrapy.Spider):
    """
    Spider for REST API content
    """
    name = "api_spider"
    
    def __init__(self, *args, **kwargs):
        super(APISpider, self).__init__(*args, **kwargs)
        self.urls = kwargs.get('urls', [])
        
    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'original_url': url}
            )
            
    def parse(self, response):
        """Parse the JSON response"""
        try:
            data = json.loads(response.text)
        except:
            data = response.text
            
        item = {
            'source_url': response.meta.get('original_url'),
            'final_url': response.url,
            'http_status': response.status,
            'content_type': 'application/json',
            'data': data,
            'download_timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        yield item
