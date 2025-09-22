"""
MetaFederate Database Module
Database abstraction layer and connection management.

Key Responsibilities:
- Database connection pooling
- Query execution and transaction management
- Connection health checking
- Database migration support

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

import logging
import asyncpg
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

class Database:
    """Database connection and query management."""
    
    def __init__(self, connection_string: str, max_connections: int = 20):
        self.connection_string = connection_string
        self.max_connections = max_connections
        self.pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> None:
        """Establish database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=self.max_connections,
                command_timeout=60,
                max_inactive_connection_lifetime=300
            )
            self.logger.info("Database connection pool established")
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self.logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions."""
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                yield connection
    
    async def execute(self, query: str, *args) -> str:
        """Execute a database query."""
        async with self.pool.acquire() as connection:
            result = await connection.execute(query, *args)
            return result
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows from database."""
        async with self.pool.acquire() as connection:
            result = await connection.fetch(query, *args)
            return result
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch single row from database."""
        async with self.pool.acquire() as connection:
            result = await connection.fetchrow(query, *args)
            return result
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch single value from database."""
        async with self.pool.acquire() as connection:
            result = await connection.fetchval(query, *args)
            return result
    
    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            async with self.pool.acquire() as connection:
                result = await connection.fetchval("SELECT 1")
                return result == 1
        except Exception:
            return False

class Logger:
    """Structured logging for database operations and security events."""
    
    def __init__(self, log_file: str = "metafederate.log"):
        self.logger = logging.getLogger("MetaFederate")
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log(self, level: str, message: str, extra: Optional[Dict] = None) -> None:
        """Log message with specified level."""
        log_method = getattr(self.logger, level.lower())
        log_method(message, extra=extra)
    
    def info(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log informational message."""
        self.log('info', message, extra)
    
    def warning(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log warning message."""
        self.log('warning', message, extra)
    
    def error(self, message: str, extra: Optional[Dict] = None) -> None:
        """Log error message."""
        self.log('error', message, extra)
    
    def security(self, event: str, user: Optional[str] = None, 
                ip: Optional[str] = None, details: Optional[Dict] = None) -> None:
        """Log security-related event."""
        extra = {
            'event_type': 'security',
            'user': user,
            'ip_address': ip,
            'details': details or {}
        }
        self.logger.info(f"Security event: {event}", extra=extra)
