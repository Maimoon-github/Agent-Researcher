
import asyncio
import httpx
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

async def test_search():
    query = "Impact of climate change on biodiversity"
    headers = {'User-Agent': "ResearchAgent/1.0"}
    timeout = 15
    
    # Wiki
    wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote_plus(query)}&format=json"
    print(f"Testing Wiki: {wiki_url}")
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(wiki_url, headers=headers)
        print(f"Wiki Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Wiki Data: {str(r.json())[:200]}...")
            
    # Arxiv
    arxiv_url = f"http://export.arxiv.org/api/query?search_query=all:{quote_plus(query)}&max_results=5"
    print(f"Testing Arxiv: {arxiv_url}")
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(arxiv_url, headers=headers)
        print(f"Arxiv Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Arxiv Data length: {len(r.text)}")

    # DDG
    ddg_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    print(f"Testing DDG: {ddg_url}")
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        r = await client.get(ddg_url, headers=headers)
        print(f"DDG Status: {r.status_code}")
        print(f"DDG Content Length: {len(r.text)}")
        if "result" in r.text.lower():
            print("DDG has results!")

if __name__ == "__main__":
    asyncio.run(test_search())
