"""
Search Service Module

This module handles web searching using the Tavily API.
"""

from typing import Dict, List, Optional

from tavily import TavilyClient

from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class SearchService:
    """Service for web searching using Tavily API."""
    
    def __init__(self):
        """Initialize the search service."""
        self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    
    async def find_information(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced"
    ) -> str:
        """
        Search for information using Tavily API.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            search_depth: Search depth (basic or advanced)
        
        Returns:
            Concatenated search results as a string
        """
        try:
            # Perform search
            response = await self._search(
                query=query,
                max_results=max_results,
                search_depth=search_depth
            )
            
            # Extract and format results
            formatted_results = self._format_results(response)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching for '{query}': {str(e)}")
            return ""
    
    async def _search(
        self,
        query: str,
        max_results: int,
        search_depth: str
    ) -> Dict:
        """Perform search using Tavily API."""
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_domains=None,  # Add specific domains if needed
                exclude_domains=None,  # Add domains to exclude if needed
                include_answer=True,
                include_raw_content=True,
                include_images=False
            )
            return response
            
        except Exception as e:
            logger.error(f"Tavily API error: {str(e)}")
            raise
    
    def _format_results(self, response: Dict) -> str:
        """Format search results into a readable string."""
        formatted_parts = []
        
        # Add AI-generated answer if available
        if response.get("answer"):
            formatted_parts.append(
                f"Summary: {response['answer']}\n"
            )
        
        # Add individual search results
        for result in response.get("results", []):
            # Format result content
            content = result.get("content", "").strip()
            url = result.get("url", "")
            title = result.get("title", "")
            
            formatted_result = f"""
Title: {title}
URL: {url}
Content: {content}
---"""
            formatted_parts.append(formatted_result)
        
        return "\n".join(formatted_parts)
    
    async def find_related_urls(
        self,
        query: str,
        max_results: int = 10
    ) -> List[str]:
        """Find related URLs for a given query."""
        try:
            response = await self._search(
                query=query,
                max_results=max_results,
                search_depth="basic"
            )
            
            # Extract URLs from results
            urls = [
                result["url"]
                for result in response.get("results", [])
                if result.get("url")
            ]
            
            return urls
            
        except Exception as e:
            logger.error(f"Error finding related URLs for '{query}': {str(e)}")
            return []
    
    async def research_topic(
        self,
        topic: str,
        aspects: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Perform comprehensive research on a topic.
        
        Args:
            topic: Main topic to research
            aspects: Specific aspects to research
        
        Returns:
            Dictionary mapping aspects to research results
        """
        results = {}
        
        try:
            # Research main topic
            main_results = await self.find_information(
                query=topic,
                max_results=3,
                search_depth="advanced"
            )
            results["overview"] = main_results
            
            # Research specific aspects if provided
            if aspects:
                for aspect in aspects:
                    aspect_query = f"{topic} {aspect}"
                    aspect_results = await self.find_information(
                        query=aspect_query,
                        max_results=2,
                        search_depth="basic"
                    )
                    results[aspect] = aspect_results
            
            return results
            
        except Exception as e:
            logger.error(f"Error researching topic '{topic}': {str(e)}")
            return {"error": str(e)} 