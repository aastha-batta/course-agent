import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
import aiohttp
import config

class ResearchService:
    """Service for gathering research from multiple sources"""
    
    def __init__(self, tavily_api_key=None):
        self.tavily_api_key = config.TAVILY_API_KEY
    
    async def search_tavily(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search the web using Tavily API"""
        if not self.tavily_api_key:
            return [{"title": "Tavily API key not configured", "content": "Please set TAVILY_API_KEY in your environment variables."}]
            
        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.tavily_api_key
            }
            
            data = {
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.tavily.com/search",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        return [{"title": f"Error: {response.status}", "content": await response.text()}]
                    
                    result = await response.json()
                    return [{"title": r.get("title", ""), "content": r.get("content", ""), "url": r.get("url", "")} 
                            for r in result.get("results", [])]
        except Exception as e:
            return [{"title": "Error", "content": f"Failed to search Tavily: {str(e)}"}]
    
    async def search_arxiv(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search academic papers on arXiv"""
        try:
            # URL encode the query
            encoded_query = urllib.parse.quote(query)
            url = f'http://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return [{"title": f"Error: {response.status}", "content": await response.text()}]
                    
                    data = await response.text()
                    
                    # Parse XML response
                    root = ET.fromstring(data)
                    namespace = {'ns': 'http://www.w3.org/2005/Atom'}
                    entries = root.findall('.//ns:entry', namespace)
                    
                    results = []
                    for entry in entries:
                        title = entry.find('./ns:title', namespace)
                        summary = entry.find('./ns:summary', namespace)
                        link = entry.find('./ns:link[@title="pdf"]', namespace)
                        
                        if title is not None and summary is not None:
                            results.append({
                                "title": title.text.strip() if title.text else "",
                                "content": summary.text.strip() if summary.text else "",
                                "url": link.attrib.get('href') if link is not None else ""
                            })
                    
                    return results
        except Exception as e:
            return [{"title": "Error", "content": f"Failed to search arXiv: {str(e)}"}]
    
    async def gather_research(self, topic: str, depth: str = "intermediate") -> Dict[str, Any]:
        """Gather research from multiple sources"""
        # Adjust search queries based on depth
        base_query = f"{topic}"
        academic_query = f"{topic} education {'advanced concepts' if depth == 'advanced' else 'basics' if depth == 'beginner' else ''}"
        
        # Collect results from different sources
        web_results = await self.search_tavily(base_query)
        academic_results = await self.search_arxiv(academic_query)
        
        # Combine and format the results
        return {
            "topic": topic,
            "depth": depth,
            "web_sources": web_results,
            "academic_sources": academic_results
        }