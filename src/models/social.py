"""
MetaFederate Social Model
Social graph management for followers, blocks, and relationships.

Key Responsibilities:
- Follow/unfollow operations
- Block/unblock management
- Relationship status checking
- Social graph traversal

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

from typing import Set, Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
from ..core.database import Database

class RelationshipStatus(Enum):
    """Relationship status between users."""
    FOLLOWING = "following"
    FOLLOWED_BY = "followed_by"
    BLOCKING = "blocking"
    BLOCKED_BY = "blocked_by"
    MUTUAL = "mutual"
    NONE = "none"
    REQUESTED = "requested"
    MUTED = "muted"

class SocialGraph:
    """Social graph management for user relationships."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def follow(self, user_address: str, target_address: str) -> bool:
        """Follow another user across platforms."""
        if user_address == target_address:
            return False
        
        # Check if already following or blocked
        current_status = await self.get_relationship(user_address, target_address)
        if current_status in [RelationshipStatus.FOLLOWING, RelationshipStatus.BLOCKING]:
            return False
        
        # Store follow relationship
        result = await self.db.execute(
            """INSERT INTO user_relationships 
            (user_address, target_user, relationship_type, created_at)
            VALUES ($1, $2, 'follow', $3)
            ON CONFLICT (user_address, target_user) 
            DO UPDATE SET relationship_type = 'follow', created_at = $3""",
            user_address, target_address, datetime.utcnow()
        )
        
        return "INSERT" in result or "UPDATE" in result
    
    async def unfollow(self, user_address: str, target_address: str) -> bool:
        """Unfollow another user."""
        result = await self.db.execute(
            """DELETE FROM user_relationships 
            WHERE user_address = $1 AND target_user = $2 
            AND relationship_type = 'follow'""",
            user_address, target_address
        )
        
        return "DELETE 1" in result
    
    async def block(self, user_address: str, target_address: str) -> bool:
        """Block another user across platforms."""
        if user_address == target_address:
            return False
        
        # Remove any existing follow relationships
        await self.unfollow(user_address, target_address)
        await self.unfollow(target_address, user_address)
        
        # Store block relationship
        result = await self.db.execute(
            """INSERT INTO user_relationships 
            (user_address, target_user, relationship_type, created_at)
            VALUES ($1, $2, 'block', $3)
            ON CONFLICT (user_address, target_user) 
            DO UPDATE SET relationship_type = 'block', created_at = $3""",
            user_address, target_address, datetime.utcnow()
        )
        
        return "INSERT" in result or "UPDATE" in result
    
    async def unblock(self, user_address: str, target_address: str) -> bool:
        """Unblock another user."""
        result = await self.db.execute(
            """DELETE FROM user_relationships 
            WHERE user_address = $1 AND target_user = $2 
            AND relationship_type = 'block'""",
            user_address, target_address
        )
        
        return "DELETE 1" in result
    
    async def get_relationship(self, user_address: str, 
                             target_address: str) -> RelationshipStatus:
        """Get relationship status between two users."""
        if user_address == target_address:
            return RelationshipStatus.NONE
        
        # Check both directions
        relationship = await self.db.fetchrow(
            """SELECT relationship_type FROM user_relationships 
            WHERE user_address = $1 AND target_user = $2""",
            user_address, target_address
        )
        
        if relationship:
            rel_type = relationship['relationship_type']
            if rel_type == 'follow':
                return RelationshipStatus.FOLLOWING
            elif rel_type == 'block':
                return RelationshipStatus.BLOCKING
        
        # Check if target follows user
        target_relationship = await self.db.fetchrow(
            """SELECT relationship_type FROM user_relationships 
            WHERE user_address = $1 AND target_user = $2""",
            target_address, user_address
        )
        
        if target_relationship:
            rel_type = target_relationship['relationship_type']
            if rel_type == 'follow':
                return RelationshipStatus.FOLLOWED_BY
            elif rel_type == 'block':
                return RelationshipStatus.BLOCKED_BY
        
        return RelationshipStatus.NONE
    
    async def get_followers(self, user_address: str, 
                          limit: int = 100, 
                          offset: int = 0) -> List[str]:
        """Get list of followers for a user."""
        followers = await self.db.fetch(
            """SELECT user_address FROM user_relationships 
            WHERE target_user = $1 AND relationship_type = 'follow'
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3""",
            user_address, limit, offset
        )
        
        return [f['user_address'] for f in followers]
    
    async def get_following(self, user_address: str,
                          limit: int = 100,
                          offset: int = 0) -> List[str]:
        """Get list of users followed by a user."""
        following = await self.db.fetch(
            """SELECT target_user FROM user_relationships 
            WHERE user_address = $1 AND relationship_type = 'follow'
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3""",
            user_address, limit, offset
        )
        
        return [f['target_user'] for f in following]
    
    async def get_blocks(self, user_address: str,
                       limit: int = 100,
                       offset: int = 0) -> List[str]:
        """Get list of users blocked by a user."""
        blocks = await self.db.fetch(
            """SELECT target_user FROM user_relationships 
            WHERE user_address = $1 AND relationship_type = 'block'
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3""",
            user_address, limit, offset
        )
        
        return [b['target_user'] for b in blocks]
    
    async def get_mutual_follows(self, user_address: str,
                               limit: int = 100,
                               offset: int = 0) -> List[str]:
        """Get list of mutual followers."""
        mutuals = await self.db.fetch(
            """SELECT ur1.target_user
            FROM user_relationships ur1
            JOIN user_relationships ur2 
            ON ur1.user_address = ur2.target_user AND ur1.target_user = ur2.user_address
            WHERE ur1.user_address = $1 
            AND ur1.relationship_type = 'follow'
            AND ur2.relationship_type = 'follow'
            ORDER BY ur1.created_at DESC
            LIMIT $2 OFFSET $3""",
            user_address, limit, offset
        )
        
        return [m['target_user'] for m in mutuals]
