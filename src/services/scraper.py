"""
Web Scraper Service Module

This module handles web scraping using Nodriver for authenticated and dynamic websites.
"""

import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from nodriver.browser import NoDriver
from nodriver.caseless import CaselessDict

from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class WebScraper:
    """Service for web scraping using Nodriver."""
    
    def __init__(self):
        """Initialize the web scraper."""
        self.driver = NoDriver()
        self.session_cookies = CaselessDict()
    
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
            # Configure driver
            self.driver.set_user_agent(settings.USER_AGENT)
            self.driver.set_timeout(settings.DEFAULT_TIMEOUT)
            
            # Handle authentication if needed
            if auth_credentials:
                await self._handle_authentication(url, auth_credentials)
            
            # Navigate to URL
            response = await self.driver.get(url)
            
            if not response.ok:
                logger.error(f"Failed to load URL {url}: {response.status_code}")
                return {"items": []}
            
            # Extract content
            content = await self._extract_content(selectors)
            
            # Store cookies for future requests
            self.session_cookies.update(self.driver.get_cookies())
            
            return {"items": content}
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return {"items": []}
        finally:
            await self.driver.close()
    
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
            
            response = await self.driver.get(login_url)
            if not response.ok:
                raise Exception(f"Failed to load login page: {response.status_code}")
            
            # Find and fill login form
            username_field = await self.driver.find_element('input[type="text"]')
            password_field = await self.driver.find_element('input[type="password"]')
            submit_button = await self.driver.find_element('button[type="submit"]')
            
            if not all([username_field, password_field, submit_button]):
                raise Exception("Could not find login form elements")
            
            # Fill credentials
            await username_field.type(credentials.get("username", ""))
            await password_field.type(credentials.get("password", ""))
            await submit_button.click()
            
            # Wait for navigation
            await asyncio.sleep(2)
            
            # Check if login was successful
            if "/login" in self.driver.current_url:
                raise Exception("Login failed - still on login page")
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    async def _extract_content(
        self,
        selectors: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Extract content using provided selectors or default extraction."""
        try:
            if selectors:
                return await self._extract_with_selectors(selectors)
            else:
                return await self._extract_default()
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            return []
    
    async def _extract_with_selectors(
        self,
        selectors: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Extract content using specific CSS selectors."""
        items = []
        
        try:
            # Find all item containers
            containers = await self.driver.find_elements(
                selectors.get("container", "article")
            )
            
            for container in containers:
                item = {}
                
                # Extract each field using its selector
                for field, selector in selectors.items():
                    if field == "container":
                        continue
                        
                    elements = await container.find_elements(selector)
                    if elements:
                        # Handle different field types
                        if field.endswith("_url"):
                            value = await elements[0].get_attribute("href")
                            value = urljoin(self.driver.current_url, value)
                        elif field.endswith("_image"):
                            value = await elements[0].get_attribute("src")
                            value = urljoin(self.driver.current_url, value)
                        else:
                            value = await elements[0].text
                        
                        item[field] = value
                
                if item:
                    items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error extracting with selectors: {str(e)}")
            return []
    
    async def _extract_default(self) -> List[Dict[str, Any]]:
        """Extract content using default extraction strategy."""
        items = []
        
        try:
            # Extract main content area
            main_content = await self.driver.find_elements("main, article, .content")
            
            if not main_content:
                main_content = await self.driver.find_elements("body")
            
            for section in main_content:
                # Extract text content
                text_content = await section.text
                
                # Extract links
                links = await section.find_elements("a")
                urls = []
                for link in links:
                    href = await link.get_attribute("href")
                    if href:
                        urls.append(urljoin(self.driver.current_url, href))
                
                # Extract images
                images = await section.find_elements("img")
                image_urls = []
                for img in images:
                    src = await img.get_attribute("src")
                    if src:
                        image_urls.append(urljoin(self.driver.current_url, src))
                
                items.append({
                    "text": text_content,
                    "urls": urls,
                    "images": image_urls
                })
            
            return items
            
        except Exception as e:
            logger.error(f"Error in default extraction: {str(e)}")
            return [] 