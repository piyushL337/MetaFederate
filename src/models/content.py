"""
MetaFederate Content Model
Content management for posts, stories, and various content types.

Key Responsibilities:
- Content creation and management
- Privacy enforcement
- Content federation
- Timeline generation

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timedelta
import uuid
import json
from ..core.database import Database

class ContentType(Enum):
    """Supported content types."""
    POST = "post"
    STORY = "story"
    REEL = "reel"
    ARTICLE = "article"
    POLL = "poll"
    EVENT = "event"
    THREAD = "thread"

class PrivacyLevel(Enum):
    """Privacy levels for content."""
    PUBLIC = "public"
    FOLLOWERS = "followers"
    PRIVATE = "private"
    MUTUAL = "mutual"
    DIRECT = "direct"

class ContentManager:
    """Content management operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create_content(self, author: str, content: str,
                          content_type: ContentType = ContentType.POST,
                          privacy: PrivacyLevel = PrivacyLevel.PUBLIC,
                          media_urls: Optional[List[str]] = None,
                          in_reply_to: Optional[str] = None,
                          expires_in: Optional[int] = None) -> Dict[str, Any]:
        """Create new federated content."""
        content_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        if expires_in:
            expires_at = created_at + timedelta(seconds=expires_in)
        else:
            expires_at = None
        
        await self.db.execute(
            """INSERT INTO federated_content 
            (id, author, content_type, content, privacy_level, 
             media_urls, in_reply_to, expires_at, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            content_id, author, content_type.value, content, privacy.value,
            json.dumps(media_urls or []), in_reply_to, expires_at, created_at
        )
        
        return {
            'id': content_id,
            'author': author,
            'content_type': content_type.value,
            'content': content,
            'privacy_level': privacy.value,
            'media_urls': media_urls or [],
            'in_reply_to': in_reply_to,
            'expires_at': expires_at.isoformat() if expires_at else None,
            'created_at': created_at.isoformat()
        }
    
    async def get_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Get content by ID."""
        content = await self.db.fetchrow(
            """SELECT id, author, content_type, content, privacy_level,
                      media_urls, in_reply_to, expires_at, created_at,
                      like_count, comment_count, repost_count, quote_count
            FROM federated_content 
            WHERE id = $1 AND (expires_at IS NULL OR expires_at > NOW())""",
            content_id
        )
        
        if not content:
            return None
        
        return dict(content)
    
    async def delete_content(self, content_id: str, author: str) -> bool:
        """Delete content by author."""
        result = await self.db.execute(
            "DELETE FROM federated_content WHERE id = $1 AND author = $2",
            content_id, author
        )
        
        return "DELETE 1" in result
    
    async def get_timeline(self, user_address: str, 
                         limit: int = 50,
                         offset: int = 0) -> List[Dict[str, Any]]:
        """Get timeline for user including federated content."""
        timeline = await self.db.fetch(
            """SELECT id, author, content_type, content, privacy_level,
                      media_urls, in_reply_to, created_at,
                      like_count, comment_count, repost_count, quote_count
            FROM federated_content 
            WHERE (privacy_level = 'public' OR author = $1)
            AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3""",
            user_address, limit, offset
        )
        
        return [dict(item) for item in timeline]
    
    async def get_user_content(self, user_address: str,
                            content_type: Optional[ContentType] = None,
                            limit: int = 50,
                            offset: int = 0) -> List[Dict[str, Any]]:
        """Get content by a specific user."""
        if content_type:
            query = """SELECT id, author, content_type, content, privacy_level,
                              media_urls, in_reply_to, created_at,
                              like_count, comment_count, repost_count, quote_count
                    FROM federated_content 
                    WHERE author = $1 AND content_type = $2
                    AND (expires_at IS NULL OR expires_at > NOW())
                    ORDER BY created_at DESC
                    LIMIT $3 OFFSET $4"""
            content = await self.db.fetch(
                query, user_address, content_type.value, limit, offset
            )
        else:
            query = """SELECT id, author, content_type, content, privacy_level,
                              media_urls, in_reply_to, created_at,
                              like_count, comment_count, repost_count, quote_count
                    FROM federated_content 
                    WHERE author = $1
                    AND (expires_at IS NULL OR expires_at > NOW())
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3"""
            content = await self.db.fetch(
                query, user_address, limit, offset
            )
        
        return [dict(item) for item in content]
    
    async def update_content_stats(self, content_id: str,
                                like_delta: int = 0,
                                comment_delta: int = 0,
                                repost_delta: int = 0,
                                quote_delta: int = 0) -> bool:
        """Update content interaction statistics."""
        result = await self.db.execute(
            """UPDATE federated_content 
            SET like_count = like_count + $2,
                comment_count = comment_count + $3,
                repost_count = repost_count + $4,
                quote_count = quote_count + $5,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1""",
            content_id, like_delta, comment_delta, repost_delta, quote_delta
        )
        
        return "UPDATE 1" in result
    
    async def cleanup_expired_content(self) -> int:
        """Clean up expired content and return number of deleted items."""
        result = await self.db.execute(
            "DELETE FROM federated_content WHERE expires_at <= NOW()"
        )
        
        if result.startswith("DELETE"):
            return int(result.split()[1])
        return 0
