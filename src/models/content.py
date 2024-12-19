"""
Content Models Module

This module defines the Pydantic models for content requests and responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl

class ContentField(BaseModel):
    """Model for a single content field."""
    name: str
    value: Any
    type: str = Field(description="Data type of the field (text, image, etc.)")
    source: Optional[str] = Field(
        None,
        description="Source of the content (URL, generated, etc.)"
    )

class ContentRequest(BaseModel):
    """Model for content retrieval request."""
    url: HttpUrl
    instructions: str
    auth_credentials: Optional[Dict[str, str]] = None
    fields_to_extract: List[str]

class ContentResponse(BaseModel):
    """Model for content retrieval response."""
    task_id: str = Field(description="Unique identifier for the task")
    status: str = Field(description="Status of the content retrieval task")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    content: List[Dict[str, ContentField]] = Field(
        description="List of retrieved content items"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the content"
    )

class DialogueMessage(BaseModel):
    """Model for dialogue messages between agent and user."""
    sender: str = Field(description="Message sender (agent/user)")
    message: str = Field(description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: str = Field(
        description="Type of message (question, instruction, response, etc.)"
    )
    requires_response: bool = Field(
        default=False,
        description="Whether this message requires a response"
    )

class ContentTable(BaseModel):
    """Model for the final content table output."""
    columns: List[str] = Field(description="Column names in the table")
    rows: List[Dict[str, Any]] = Field(description="Row data")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Table metadata"
    ) 