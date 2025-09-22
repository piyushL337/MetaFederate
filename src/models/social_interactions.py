"""
MetaFederate Social Interactions Model
Handles likes, comments, reposts, quotes, and other social interactions.

Key Responsibilities:
- Like/unlike operations
- Comment management
- Repost handling
- Quote post creation
- Interaction statistics

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import uuid
import json
from ..core.database import Database

class InteractionType(Enum):
    """Types of social interactions."""
    LIKE = "like"
    COMMENT = "comment"
    REPOST = "repost"
    QUOTE = "quote"
    REACTION = "reaction"

class SocialInteractions:
    """Social interaction management operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def like_content(self, user_address: str, content_id: str,
                         reaction: str = "❤️") -> Dict[str, Any]:
        """Like content across platforms."""
        # Check if already liked
        existing = await self.db.fetchval(
            """SELECT id FROM content_interactions 
            WHERE content_id = $1 AND user_address = $2 AND interaction_type = 'like'""",
            content_id, user_address
        )
        
        if existing:
            return {"status": "already_liked", "like_id": existing}
        
        like_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        await self.db.execute(
            """INSERT INTO content_interactions 
            (id, content_id, user_address, interaction_type, interaction_data, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)""",
            like_id, content_id, user_address, 'like',
            json.dumps({"reaction": reaction}), created_at
        )
        
        # Update like count
        await self.db.execute(
            "UPDATE federated_content SET like_count = like_count + 1 WHERE id = $1",
            content_id
        )
        
        return {"status": "liked", "like_id": like_id}
    
    async def unlike_content(self, user_address: str, content_id: str) -> Dict[str, Any]:
        """Remove like from content."""
        result = await self.db.execute(
            """DELETE FROM content_interactions 
            WHERE content_id = $1 AND user_address = $2 AND interaction_type = 'like'""",
            content_id, user_address
        )
        
        if "DELETE 1" in result:
            # Update like count
            await self.db.execute(
                "UPDATE federated_content SET like_count = like_count - 1 WHERE id = $1",
                content_id
            )
            return {"status": "unliked"}
        
        return {"status": "not_liked"}
    
    async def comment_content(self, user_address: str, content_id: str,
                            comment_text: str,
                            parent_comment_id: Optional[str] = None,
                            media_urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """Add comment to content."""
        comment_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        await self.db.execute(
            """INSERT INTO comments 
            (id, content_id, user_address, comment_text, parent_comment_id, media_urls, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            comment_id, content_id, user_address, comment_text,
            parent_comment_id, json.dumps(media_urls or []), created_at
        )
        
        # Update comment count
        await self.db.execute(
            "UPDATE federated_content SET comment_count = comment_count + 1 WHERE id = $1",
            content_id
        )
        
        return {"status": "commented", "comment_id": comment_id}
    
    async def delete_comment(self, comment_id: str, user_address: str) -> bool:
        """Delete comment by author."""
        # Get comment to find content ID
        comment = await self.db.fetchrow(
            "SELECT content_id FROM comments WHERE id = $1 AND user_address = $2",
            comment_id, user_address
        )
        
        if not comment:
            return False
        
        result = await self.db.execute(
            "DELETE FROM comments WHERE id = $1 AND user_address = $2",
            comment_id, user_address
        )
        
        if "DELETE 1" in result:
            # Update comment count
            await self.db.execute(
                "UPDATE federated_content SET comment_count = comment_count - 1 WHERE id = $1",
                comment['content_id']
            )
            return True
        
        return False
    
    async def repost_content(self, user_address: str, original_content_id: str,
                           repost_text: Optional[str] = None) -> Dict[str, Any]:
        """Repost content to user's profile."""
        # Check if already reposted
        existing = await self.db.fetchval(
            """SELECT id FROM reposts 
            WHERE original_content_id = $1 AND user_address = $2""",
            original_content_id, user_address
        )
        
        if existing:
            return {"status": "already_reposted", "repost_id": existing}
        
        repost_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        await self.db.execute(
            """INSERT INTO reposts 
            (id, original_content_id, user_address, repost_text, created_at)
            VALUES ($1, $2, $3, $4, $5)""",
            repost_id, original_content_id, user_address, repost_text, created_at
        )
        
        # Update repost count
        await self.db.execute(
            "UPDATE federated_content SET repost_count = repost_count + 1 WHERE id = $1",
            original_content_id
        )
        
        return {"status": "reposted", "repost_id": repost_id}
    
    async def quote_content(self, user_address: str, original_content_id: str,
                          quote_text: str, new_content_id: str) -> Dict[str, Any]:
        """Create quote post referencing original content."""
        quote_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        await self.db.execute(
            """INSERT INTO quotes 
            (id, original_content_id, quote_content_id, user_address, quote_text, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)""",
            quote_id, original_content_id, new_content_id, user_address, quote_text, created_at
        )
        
        # Update quote count
        await self.db.execute(
            "UPDATE federated_content SET quote_count = quote_count + 1 WHERE id = $1",
            original_content_id
        )
        
        return {"status": "quoted", "quote_id": quote_id}
    
    async def get_content_interactions(self, content_id: str,
                                    interaction_type: Optional[InteractionType] = None,
                                    limit: int = 100,
                                    offset: int = 0) -> List[Dict[str, Any]]:
        """Get interactions for specific content."""
        if interaction_type:
            query = """SELECT ci.id, ci.user_address, ci.interaction_type, 
                              ci.interaction_data, ci.created_at
                    FROM content_interactions ci
                    WHERE ci.content_id = $1 AND ci.interaction_type = $2
                    ORDER BY ci.created_at DESC
                    LIMIT $3 OFFSET $4"""
            interactions = await self.db.fetch(
                query, content_id, interaction_type.value, limit, offset
            )
        else:
            query = """SELECT ci.id, ci.user_address, ci.interaction_type, 
                              ci.interaction_data, ci.created_at
                    FROM content_interactions ci
                    WHERE ci.content_id = $1
                    ORDER BY ci.created_at DESC
                    LIMIT $2 OFFSET $3"""
            interactions = await self.db.fetch(
                query, content_id, limit, offset
            )
        
        return [dict(interaction) for interaction in interactions]
    
    async def get_user_interactions(self, user_address: str,
                                  interaction_type: Optional[InteractionType] = None,
                                  limit: int = 100,
                                  offset: int = 0) -> List[Dict[str, Any]]:
        """Get interactions by a specific user."""
        if interaction_type:
            query = """SELECT ci.id, ci.content_id, ci.interaction_type, 
                              ci.interaction_data, ci.created_at,
                              fc.content, fc.author
                    FROM content_interactions ci
                    JOIN federated_content fc ON ci.content_id = fc.id
                    WHERE ci.user_address = $1 AND ci.interaction_type = $2
                    ORDER BY ci.created_at DESC
                    LIMIT $3 OFFSET $4"""
            interactions = await self.db.fetch(
                query, user_address, interaction_type.value, limit, offset
            )
        else:
            query = """SELECT ci.id, ci.content_id, ci.interaction_type, 
                              ci.interaction_data, ci.created_at,
                              fc.content, fc.author
                    FROM content_interactions ci
                    JOIN federated_content fc ON ci.content_id = fc.id
                    WHERE ci.user_address = $1
                    ORDER BY ci.created_at DESC
                    LIMIT $2 OFFSET $3"""
            interactions = await self.db.fetch(
                query, user_address, limit, offset
            )
        
        return [dict(interaction) for interaction in interactions]
