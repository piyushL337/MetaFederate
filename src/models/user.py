"""
MetaFederate User Model
User management and federated identity handling.

Key Responsibilities:
- User registration and authentication
- Profile management
- Key pair management
- Federated identity resolution

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from ..core.crypto import Crypto
from ..core.database import Database

class FederatedUser:
    """Represents a federated user with cross-platform identity."""
    
    def __init__(self, user_id: str, username: str, domain: str, 
                 public_key: str, display_name: Optional[str] = None,
                 bio: Optional[str] = None, avatar_url: Optional[str] = None):
        self.user_id = user_id
        self.username = username
        self.domain = domain
        self.public_key = public_key
        self.display_name = display_name
        self.bio = bio
        self.avatar_url = avatar_url
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @property
    def full_address(self) -> str:
        return f"{self.username}@{self.domain}"
    
    @property
    def profile_url(self) -> str:
        return f"https://{self.domain}/users/{self.username}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        return {
            'id': self.user_id,
            'username': self.username,
            'domain': self.domain,
            'display_name': self.display_name,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'public_key': self.public_key,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class UserManager:
    """User management operations."""
    
    def __init__(self, db: Database):
        self.db = db
        self.crypto = Crypto()
    
    async def create_user(self, username: str, password: str, domain: str,
                        display_name: Optional[str] = None,
                        bio: Optional[str] = None,
                        avatar_url: Optional[str] = None) -> FederatedUser:
        """Create a new federated user."""
        # Generate user ID
        user_id = str(uuid.uuid4())
        
        # Generate key pair
        keypair = self.crypto.generate_key_pair()
        
        # Hash password
        hashed_password = self.crypto.hash_password(password)
        
        # Store user in database
        await self.db.execute(
            """INSERT INTO federated_users 
            (id, username, domain, display_name, bio, avatar_url, 
             public_key, private_key_encrypted, password_hash)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            user_id, username, domain, display_name, bio, avatar_url,
            keypair['public_key'], keypair['private_key'], hashed_password
        )
        
        return FederatedUser(
            user_id=user_id,
            username=username,
            domain=domain,
            public_key=keypair['public_key'],
            display_name=display_name,
            bio=bio,
            avatar_url=avatar_url
        )
    
    async def authenticate_user(self, username: str, password: str, 
                              domain: str) -> Optional[FederatedUser]:
        """Authenticate user with password."""
        user_data = await self.db.fetchrow(
            """SELECT id, username, domain, display_name, bio, avatar_url, 
                      public_key, password_hash
            FROM federated_users 
            WHERE username = $1 AND domain = $2""",
            username, domain
        )
        
        if not user_data:
            return None
        
        if self.crypto.verify_password(password, user_data['password_hash']):
            return FederatedUser(
                user_id=user_data['id'],
                username=user_data['username'],
                domain=user_data['domain'],
                public_key=user_data['public_key'],
                display_name=user_data['display_name'],
                bio=user_data['bio'],
                avatar_url=user_data['avatar_url']
            )
        
        return None
    
    async def get_user(self, user_address: str) -> Optional[FederatedUser]:
        """Get user by federated address."""
        if '@' not in user_address:
            return None
        
        username, domain = user_address.split('@', 1)
        
        user_data = await self.db.fetchrow(
            """SELECT id, username, domain, display_name, bio, avatar_url, public_key
            FROM federated_users 
            WHERE username = $1 AND domain = $2""",
            username, domain
        )
        
        if not user_data:
            return None
        
        return FederatedUser(
            user_id=user_data['id'],
            username=user_data['username'],
            domain=user_data['domain'],
            public_key=user_data['public_key'],
            display_name=user_data['display_name'],
            bio=user_data['bio'],
            avatar_url=user_data['avatar_url']
        )
    
    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile."""
        allowed_fields = {'display_name', 'bio', 'avatar_url'}
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not update_fields:
            return False
        
        set_clause = ", ".join([f"{field} = ${i+2}" for i, field in enumerate(update_fields)])
        values = list(update_fields.values())
        
        query = f"""
            UPDATE federated_users 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        
        result = await self.db.execute(query, user_id, *values)
        return "UPDATE 1" in result
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user account."""
        result = await self.db.execute(
            "DELETE FROM federated_users WHERE id = $1",
            user_id
        )
        return "DELETE 1" in result
