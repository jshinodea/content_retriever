"""
Web Scraper Service Module

This module handles web scraping using nodriver for authenticated and dynamic websites.
"""

import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import nodriver

from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class WebScraper:
    """Service for web scraping using nodriver."""
    
    def __init__(self):
        """Initialize the web scraper."""
        self.browser = None
    
    async def scrape(
        self,
        url: str,
        auth_credentials: Optional[Dict[str, str]] = None,
        selectors: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Scrape content from a URL.
        
        Args:
            url: Target URL to scrape
            auth_credentials: Optional credentials for authentication
            selectors: Optional CSS selectors for content extraction
        
        Returns:
            Dictionary containing scraped content
        """
        try:
            # Start browser
            self.browser = await nodriver.start()
            
            # Handle authentication if needed
            if auth_credentials:
                await self._handle_authentication(url, auth_credentials)
            
            # Navigate to URL
            page = await self.browser.get(url)
            
            # Wait for content to load
            content = await page.get_content()
            if not content:
                logger.error(f"Failed to load URL {url}")
                return {"items": []}
            
            # Extract content
            items = await self._extract_content(page, selectors)
            
            return {"items": items}
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return {"items": []}
        finally:
            if self.browser:
                await self.browser.close()
    
    async def _handle_authentication(
        self,
        url: str,
        credentials: Dict[str, str]
    ) -> None:
        """Handle website authentication."""
        try:
            # Load login page
            domain = urlparse(url).netloc
            login_url = f"https://{domain}/login"  # Adjust based on site
            
            login_page = await self.browser.get(login_url)
            
            # Find and fill login form
            username_field = await login_page.select('input[type="text"]')
            password_field = await login_page.select('input[type="password"]')
            submit_button = await login_page.select('button[type="submit"]')
            
            if not all([username_field, password_field, submit_button]):
                raise Exception("Could not find login form elements")
            
            # Fill credentials
            await username_field[0].type(credentials.get("username", ""))
            await password_field[0].type(credentials.get("password", ""))
            await submit_button[0].click()
            
            # Wait for navigation
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    async def _extract_content(
        self,
        page,
        selectors: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Extract content using provided selectors or default extraction."""
        try:
            if selectors:
                return await self._extract_with_selectors(page, selectors)
            else:
                return await self._extract_default(page)
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            return []
    
    async def _extract_with_selectors(
        self,
        page,
        selectors: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Extract content using specific CSS selectors."""
        items = []
        
        try:
            # Find all item containers
            containers = await page.select_all(selectors.get("container", "article"))
            
            for container in containers:
                item = {}
                
                # Extract each field using its selector
                for field, selector in selectors.items():
                    if field == "container":
                        continue
                        
                    elements = await container.select_all(selector)
                    if elements:
                        element = elements[0]
                        # Handle different field types
                        if field.endswith("_url"):
                            value = await element.get_attribute("href")
                            value = urljoin(page.url, value)
                        elif field.endswith("_image"):
                            value = await element.get_attribute("src")
                            value = urljoin(page.url, value)
                        else:
                            value = await element.text()
                        
                        item[field] = value
                
                if item:
                    items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error extracting with selectors: {str(e)}")
            return []
    
    async def _extract_default(self, page) -> List[Dict[str, Any]]:
        """Extract content using default extraction strategy."""
        items = []
        
        try:
            # Extract main content area
            main_content = await page.select_all("main, article, .content")
            
            if not main_content:
                main_content = await page.select_all("body")
            
            for section in main_content:
                # Extract text content
                text_content = await section.text()
                
                # Extract links
                links = await section.select_all("a")
                urls = []
                for link in links:
                    href = await link.get_attribute("href")
                    if href:
                        urls.append(urljoin(page.url, href))
                
                # Extract images
                images = await section.select_all("img")
                image_urls = []
                for img in images:
                    src = await img.get_attribute("src")
                    if src:
                        image_urls.append(urljoin(page.url, src))
                
                items.append({
                    "text": text_content,
                    "urls": urls,
                    "images": image_urls
                })
            
            return items
            
        except Exception as e:
            logger.error(f"Error in default extraction: {str(e)}")
            return [] 