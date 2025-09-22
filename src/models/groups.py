"""
MetaFederate Groups Model
Group and community management for federated platforms.

Key Responsibilities:
- Group creation and management
- Membership management
- Group content sharing
- Moderation tools

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import uuid
import json
from ..core.database import Database

class GroupPrivacy(Enum):
    """Group privacy levels."""
    PUBLIC = "public"
    PRIVATE = "private"
    SECRET = "secret"

class GroupRole(Enum):
    """Group member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"

class Group:
    """Represents a federated group or community."""
    
    def __init__(self, group_id: str, name: str, description: str,
                 creator: str, privacy: GroupPrivacy = GroupPrivacy.PUBLIC,
                 avatar_url: Optional[str] = None,
                 banner_url: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 member_count: int = 0):
        self.group_id = group_id
        self.name = name
        self.description = description
        self.creator = creator
        self.privacy = privacy
        self.avatar_url = avatar_url
        self.banner_url = banner_url
        self.created_at = created_at or datetime.utcnow()
        self.member_count = member_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert group to dictionary representation."""
        return {
            'id': self.group_id,
            'name': self.name,
            'description': self.description,
            'creator': self.creator,
            'privacy': self.privacy.value,
            'avatar_url': self.avatar_url,
            'banner_url': self.banner_url,
            'created_at': self.created_at.isoformat(),
            'member_count': self.member_count
        }

class GroupMembership:
    """Represents a user's membership in a group."""
    
    def __init__(self, group_id: str, user_address: str,
                 role: GroupRole = GroupRole.MEMBER,
                 joined_at: Optional[datetime] = None,
                 is_banned: bool = False):
        self.group_id = group_id
        self.user_address = user_address
        self.role = role
        self.joined_at = joined_at or datetime.utcnow()
        self.is_banned = is_banned
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert membership to dictionary representation."""
        return {
            'group_id': self.group_id,
            'user_address': self.user_address,
            'role': self.role.value,
            'joined_at': self.joined_at.isoformat(),
            'is_banned': self.is_banned
        }

class GroupManager:
    """Group management operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create_group(self, name: str, description: str, creator: str,
                         privacy: GroupPrivacy = GroupPrivacy.PUBLIC,
                         avatar_url: Optional[str] = None,
                         banner_url: Optional[str] = None) -> Group:
        """Create a new federated group."""
        group_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        await self.db.execute(
            """INSERT INTO groups 
            (id, name, description, creator, privacy, avatar_url, banner_url, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            group_id, name, description, creator, privacy.value,
            avatar_url, banner_url, created_at
        )
        
        # Add creator as owner
        await self.add_member(group_id, creator, GroupRole.OWNER)
        
        return Group(
            group_id=group_id,
            name=name,
            description=description,
            creator=creator,
            privacy=privacy,
            avatar_url=avatar_url,
            banner_url=banner_url,
            created_at=created_at,
            member_count=1
        )
    
    async def get_group(self, group_id: str) -> Optional[Group]:
        """Get group by ID."""
        group = await self.db.fetchrow(
            """SELECT id, name, description, creator, privacy, 
                      avatar_url, banner_url, created_at,
                      (SELECT COUNT(*) FROM group_members WHERE group_id = id) as member_count
            FROM groups 
            WHERE id = $1""",
            group_id
        )
        
        if not group:
            return None
        
        return Group(
            group_id=group['id'],
            name=group['name'],
            description=group['description'],
            creator=group['creator'],
            privacy=GroupPrivacy(group['privacy']),
            avatar_url=group['avatar_url'],
            banner_url=group['banner_url'],
            created_at=group['created_at'],
            member_count=group['member_count']
        )
    
    async def add_member(self, group_id: str, user_address: str,
                       role: GroupRole = GroupRole.MEMBER) -> bool:
        """Add user to group."""
        result = await self.db.execute(
            """INSERT INTO group_members 
            (group_id, user_address, role, joined_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (group_id, user_address) 
            DO UPDATE SET role = $3, is_banned = FALSE""",
            group_id, user_address, role.value, datetime.utcnow()
        )
        
        return "INSERT" in result or "UPDATE" in result
    
    async def remove_member(self, group_id: str, user_address: str) -> bool:
        """Remove user from group."""
        result = await self.db.execute(
            "DELETE FROM group_members WHERE group_id = $1 AND user_address = $2",
            group_id, user_address
        )
        
        return "DELETE 1" in result
    
    async def ban_member(self, group_id: str, user_address: str) -> bool:
        """Ban user from group."""
        result = await self.db.execute(
            """UPDATE group_members 
            SET is_banned = TRUE 
            WHERE group_id = $1 AND user_address = $2""",
            group_id, user_address
        )
        
        return "UPDATE 1" in result
    
    async def get_group_members(self, group_id: str,
                              limit: int = 100,
                              offset: int = 0) -> List[GroupMembership]:
        """Get members of a group."""
        members = await self.db.fetch(
            """SELECT group_id, user_address, role, joined_at, is_banned
            FROM group_members 
            WHERE group_id = $1
            ORDER BY joined_at DESC
            LIMIT $2 OFFSET $3""",
            group_id, limit, offset
        )
        
        return [
            GroupMembership(
                group_id=member['group_id'],
                user_address=member['user_address'],
                role=GroupRole(member['role']),
                joined_at=member['joined_at'],
                is_banned=member['is_banned']
            )
            for member in members
        ]
    
    async def get_user_groups(self, user_address: str,
                            limit: int = 50,
                            offset: int = 0) -> List[Group]:
        """Get groups that a user belongs to."""
        groups = await self.db.fetch(
            """SELECT g.id, g.name, g.description, g.creator, g.privacy,
                      g.avatar_url, g.banner_url, g.created_at,
                      (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count
            FROM groups g
            JOIN group_members gm ON g.id = gm.group_id
            WHERE gm.user_address = $1 AND gm.is_banned = FALSE
            ORDER BY gm.joined_at DESC
            LIMIT $2 OFFSET $3""",
            user_address, limit, offset
        )
        
        return [
            Group(
                group_id=group['id'],
                name=group['name'],
                description=group['description'],
                creator=group['creator'],
                privacy=GroupPrivacy(group['privacy']),
                avatar_url=group['avatar_url'],
                banner_url=group['banner_url'],
                created_at=group['created_at'],
                member_count=group['member_count']
            )
            for group in groups
        ]
    
    async def search_groups(self, query: str,
                          limit: int = 50,
                          offset: int = 0) -> List[Group]:
        """Search for groups by name or description."""
        search_pattern = f"%{query}%"
        
        groups = await self.db.fetch(
            """SELECT id, name, description, creator, privacy,
                      avatar_url, banner_url, created_at,
                      (SELECT COUNT(*) FROM group_members WHERE group_id = id) as member_count
            FROM groups 
            WHERE (name ILIKE $1 OR description ILIKE $1)
            AND privacy != 'secret'
            ORDER BY member_count DESC
            LIMIT $2 OFFSET $3""",
            search_pattern, limit, offset
        )
        
        return [
            Group(
                group_id=group['id'],
                name=group['name'],
                description=group['description'],
                creator=group['creator'],
                privacy=GroupPrivacy(group['privacy']),
                avatar_url=group['avatar_url'],
                banner_url=group['banner_url'],
                created_at=group['created_at'],
                member_count=group['member_count']
            )
            for group in groups
        ]
