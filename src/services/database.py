"""
Database Service Module

This module handles database operations using Cassandra for content storage.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from cassandra.cluster import Cluster, Session
from cassandra.query import SimpleStatement

from core.config import settings
from models.content import ContentField, ContentTable
from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseService:
    """Service for database operations using Cassandra."""
    
    def __init__(self):
        """Initialize the database service."""
        self.cluster = None
        self.session = None
        self._connect()
        self._setup_schema()
    
    def _connect(self) -> None:
        """Establish connection to Cassandra cluster."""
        try:
            # Connect to cluster
            self.cluster = Cluster(
                contact_points=settings.CASSANDRA_HOSTS,
                port=settings.CASSANDRA_PORT,
                auth_provider=self._get_auth_provider()
            )
            
            # Create session
            self.session = self.cluster.connect()
            
            # Create keyspace if not exists
            self._create_keyspace()
            
            # Use keyspace
            self.session.set_keyspace(settings.CASSANDRA_KEYSPACE)
            
            logger.info("Connected to Cassandra cluster")
            
        except Exception as e:
            logger.error(f"Error connecting to Cassandra: {str(e)}")
            raise
    
    def _get_auth_provider(self):
        """Get authentication provider if credentials are set."""
        if settings.CASSANDRA_USERNAME and settings.CASSANDRA_PASSWORD:
            from cassandra.auth import PlainTextAuthProvider
            return PlainTextAuthProvider(
                username=settings.CASSANDRA_USERNAME,
                password=settings.CASSANDRA_PASSWORD
            )
        return None
    
    def _create_keyspace(self) -> None:
        """Create keyspace if it doesn't exist."""
        query = f"""
        CREATE KEYSPACE IF NOT EXISTS {settings.CASSANDRA_KEYSPACE}
        WITH replication = {{
            'class': 'SimpleStrategy',
            'replication_factor': 1
        }}
        """
        self.session.execute(query)
    
    def _setup_schema(self) -> None:
        """Set up database schema."""
        # Create content_tasks table
        self.session.execute("""
        CREATE TABLE IF NOT EXISTS content_tasks (
            task_id uuid PRIMARY KEY,
            url text,
            instructions text,
            status text,
            created_at timestamp,
            updated_at timestamp,
            metadata map<text, text>
        )
        """)
        
        # Create content_items table
        self.session.execute("""
        CREATE TABLE IF NOT EXISTS content_items (
            task_id uuid,
            item_id uuid,
            field_name text,
            field_value text,
            field_type text,
            source text,
            created_at timestamp,
            PRIMARY KEY ((task_id), item_id, field_name)
        )
        """)
        
        # Create content_tables table
        self.session.execute("""
        CREATE TABLE IF NOT EXISTS content_tables (
            task_id uuid PRIMARY KEY,
            columns list<text>,
            rows list<text>,  # JSON serialized
            metadata map<text, text>,
            created_at timestamp
        )
        """)
    
    async def store_task(
        self,
        task_id: UUID,
        url: str,
        instructions: str,
        status: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> None:
        """Store task information."""
        try:
            query = """
            INSERT INTO content_tasks (
                task_id, url, instructions, status,
                created_at, updated_at, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.utcnow()
            self.session.execute(
                query,
                (task_id, url, instructions, status, now, now, metadata or {})
            )
            
        except Exception as e:
            logger.error(f"Error storing task {task_id}: {str(e)}")
            raise
    
    async def store_content_items(
        self,
        task_id: UUID,
        items: List[Dict[str, ContentField]]
    ) -> None:
        """Store content items."""
        try:
            query = """
            INSERT INTO content_items (
                task_id, item_id, field_name, field_value,
                field_type, source, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            batch = []
            now = datetime.utcnow()
            
            for item_id, item in enumerate(items):
                for field_name, field in item.items():
                    params = (
                        task_id,
                        UUID(int=item_id),  # Generate UUID from index
                        field_name,
                        str(field.value),
                        field.type,
                        field.source,
                        now
                    )
                    batch.append(params)
            
            # Execute batch insert
            prepared = self.session.prepare(query)
            for params in batch:
                self.session.execute(prepared, params)
            
        except Exception as e:
            logger.error(f"Error storing content items for task {task_id}: {str(e)}")
            raise
    
    async def store_content_table(
        self,
        task_id: UUID,
        table: ContentTable
    ) -> None:
        """Store content table."""
        try:
            query = """
            INSERT INTO content_tables (
                task_id, columns, rows, metadata, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """
            
            # Serialize rows to JSON strings
            serialized_rows = [json.dumps(row) for row in table.rows]
            
            self.session.execute(
                query,
                (
                    task_id,
                    table.columns,
                    serialized_rows,
                    table.metadata,
                    datetime.utcnow()
                )
            )
            
        except Exception as e:
            logger.error(f"Error storing content table for task {task_id}: {str(e)}")
            raise
    
    async def get_task(self, task_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve task information."""
        try:
            query = "SELECT * FROM content_tasks WHERE task_id = ?"
            result = self.session.execute(query, (task_id,)).one()
            
            if not result:
                return None
            
            return {
                "task_id": result.task_id,
                "url": result.url,
                "instructions": result.instructions,
                "status": result.status,
                "created_at": result.created_at,
                "updated_at": result.updated_at,
                "metadata": result.metadata
            }
            
        except Exception as e:
            logger.error(f"Error retrieving task {task_id}: {str(e)}")
            raise
    
    async def get_content_items(
        self,
        task_id: UUID
    ) -> List[Dict[str, ContentField]]:
        """Retrieve content items for a task."""
        try:
            query = "SELECT * FROM content_items WHERE task_id = ?"
            results = self.session.execute(query, (task_id,))
            
            # Group fields by item_id
            items: Dict[UUID, Dict[str, ContentField]] = {}
            for row in results:
                if row.item_id not in items:
                    items[row.item_id] = {}
                
                items[row.item_id][row.field_name] = ContentField(
                    name=row.field_name,
                    value=row.field_value,
                    type=row.field_type,
                    source=row.source
                )
            
            # Convert to list and sort by item_id
            return [
                items[item_id]
                for item_id in sorted(items.keys())
            ]
            
        except Exception as e:
            logger.error(f"Error retrieving content items for task {task_id}: {str(e)}")
            raise
    
    async def get_content_table(
        self,
        task_id: UUID
    ) -> Optional[ContentTable]:
        """Retrieve content table for a task."""
        try:
            query = "SELECT * FROM content_tables WHERE task_id = ?"
            result = self.session.execute(query, (task_id,)).one()
            
            if not result:
                return None
            
            # Deserialize rows from JSON
            rows = [json.loads(row) for row in result.rows]
            
            return ContentTable(
                columns=result.columns,
                rows=rows,
                metadata=result.metadata
            )
            
        except Exception as e:
            logger.error(f"Error retrieving content table for task {task_id}: {str(e)}")
            raise
    
    def close(self) -> None:
        """Close database connections."""
        if self.session:
            self.session.shutdown()
        if self.cluster:
            self.cluster.shutdown() 