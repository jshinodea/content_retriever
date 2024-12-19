"""
Content Agent Service Module

This module implements the main content retrieval and processing agent.
"""

import asyncio
import uuid
from typing import Any, Dict, List, Optional

from models.content import ContentField, ContentRequest, ContentResponse, ContentTable
from services.llm import LLMService
from services.scraper import WebScraper
from services.search import SearchService
from services.vision import VisionService
from utils.logger import get_logger

logger = get_logger(__name__)

class ContentAgent:
    """Main agent for content retrieval and processing."""
    
    def __init__(self):
        """Initialize the content agent with required services."""
        self.llm = LLMService()
        self.scraper = WebScraper()
        self.search = SearchService()
        self.vision = VisionService()
    
    async def process_task(
        self,
        url: str,
        instructions: str,
        auth_credentials: Optional[Dict[str, str]] = None
    ) -> ContentResponse:
        """Process a content retrieval task."""
        task_id = str(uuid.uuid4())
        logger.info(f"Starting task {task_id}")
        
        try:
            # Parse instructions using LLM
            fields_to_extract = await self.llm.parse_instructions(instructions)
            
            # Create content request
            request = ContentRequest(
                url=url,
                instructions=instructions,
                auth_credentials=auth_credentials,
                fields_to_extract=fields_to_extract
            )
            
            # Scrape content
            scraped_content = await self.scraper.scrape(
                url=request.url,
                auth_credentials=request.auth_credentials
            )
            
            # Process content with LLM
            processed_content = await self.process_content(
                scraped_content,
                request.fields_to_extract
            )
            
            # Create response
            response = ContentResponse(
                task_id=task_id,
                status="completed",
                content=processed_content,
                metadata={
                    "url": str(request.url),
                    "fields_extracted": fields_to_extract
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")
            raise
    
    async def process_content(
        self,
        raw_content: Dict[str, Any],
        fields_to_extract: List[str]
    ) -> List[Dict[str, ContentField]]:
        """Process raw content and extract specified fields."""
        processed_items = []
        
        for item in raw_content.get("items", []):
            processed_fields = {}
            
            for field in fields_to_extract:
                # Extract or generate content for each field
                field_content = await self._process_field(field, item)
                processed_fields[field] = field_content
            
            processed_items.append(processed_fields)
        
        return processed_items
    
    async def _process_field(self, field: str, item: Dict[str, Any]) -> ContentField:
        """Process a single content field."""
        # Check if field exists in raw content
        if field in item:
            return ContentField(
                name=field,
                value=item[field],
                type="text",
                source="extracted"
            )
        
        # If field doesn't exist, try to generate or find it
        try:
            # Search for additional information
            search_results = await self.search.find_information(
                query=f"{item.get('title', '')} {field}"
            )
            
            # Generate content using LLM
            generated_content = await self.llm.generate_content(
                field=field,
                context=search_results,
                item_data=item
            )
            
            return ContentField(
                name=field,
                value=generated_content,
                type="text",
                source="generated"
            )
            
        except Exception as e:
            logger.error(f"Error processing field {field}: {str(e)}")
            return ContentField(
                name=field,
                value=None,
                type="text",
                source="error"
            )
    
    async def create_content_table(
        self,
        content: List[Dict[str, ContentField]]
    ) -> ContentTable:
        """Create a structured table from processed content."""
        if not content:
            return ContentTable(columns=[], rows=[])
        
        # Extract column names from first item
        columns = list(content[0].keys())
        
        # Create rows
        rows = []
        for item in content:
            row = {
                field: item[field].value
                for field in columns
                if field in item
            }
            rows.append(row)
        
        return ContentTable(
            columns=columns,
            rows=rows,
            metadata={
                "total_rows": len(rows),
                "generated_fields": [
                    field
                    for field in columns
                    if any(item[field].source == "generated" for item in content)
                ]
            }
        ) 