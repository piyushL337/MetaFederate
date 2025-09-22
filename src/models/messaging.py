"""
MetaFederate Messaging Model
Direct messaging with end-to-end encryption.

Key Responsibilities:
- Encrypted message handling
- Conversation management
- Message delivery status
- Read receipts

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import json
from ..core.crypto import Crypto
from ..core.database import Database

class EncryptedMessage:
    """Represents an encrypted message between users."""
    
    def __init__(self, message_id: str, from_user: str, to_user: str,
                 encrypted_content: str, encryption_key: str, iv: str,
                 algorithm: str, message_type: str = "text",
                 attachments: Optional[List[str]] = None,
                 created_at: Optional[datetime] = None,
                 read: bool = False):
        self.message_id = message_id
        self.from_user = from_user
        self.to_user = to_user
        self.encrypted_content = encrypted_content
        self.encryption_key = encryption_key
        self.iv = iv
        self.algorithm = algorithm
        self.message_type = message_type
        self.attachments = attachments or []
        self.created_at = created_at or datetime.utcnow()
        self.read = read
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation."""
        return {
            'id': self.message_id,
            'from': self.from_user,
            'to': self.to_user,
            'encrypted_content': self.encrypted_content,
            'encryption_key': self.encryption_key,
            'iv': self.iv,
            'algorithm': self.algorithm,
            'message_type': self.message_type,
            'attachments': self.attachments,
            'created_at': self.created_at.isoformat(),
            'read': self.read
        }

class MessageManager:
    """Message management operations."""
    
    def __init__(self, db: Database):
        self.db = db
        self.crypto = Crypto()
    
    async def send_message(self, from_user: str, to_user: str,
                         content: str, message_type: str = "text",
                         attachments: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send an encrypted message to another user."""
        # Get recipient's public key
        recipient_key = await self._get_public_key(to_user)
        if not recipient_key:
            raise ValueError("Recipient public key not found")
        
        # Encrypt message
        encrypted_data = self.crypto.encrypt_message(content, recipient_key)
        
        message_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        await self.db.execute(
            """INSERT INTO direct_messages 
            (id, from_user, to_user, encrypted_content, encryption_key,
             iv, algorithm, message_type, attachments, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            message_id, from_user, to_user,
            encrypted_data['ciphertext'],
            encrypted_data['encrypted_key'],
            encrypted_data.get('iv', ''),
            encrypted_data['algorithm'],
            message_type,
            json.dumps(attachments or []),
            created_at
        )
        
        return {
            'id': message_id,
            'from': from_user,
            'to': to_user,
            'encrypted_content': encrypted_data['ciphertext'],
            'encryption_key': encrypted_data['encrypted_key'],
            'algorithm': encrypted_data['algorithm'],
            'message_type': message_type,
            'attachments': attachments or [],
            'created_at': created_at.isoformat(),
            'read': False
        }
    
    async def get_message(self, message_id: str, 
                        user_address: str) -> Optional[EncryptedMessage]:
        """Get encrypted message by ID."""
        message = await self.db.fetchrow(
            """SELECT id, from_user, to_user, encrypted_content, encryption_key,
                      iv, algorithm, message_type, attachments, created_at, read
            FROM direct_messages 
            WHERE id = $1 AND (from_user = $2 OR to_user = $2)""",
            message_id, user_address
        )
        
        if not message:
            return None
        
        return EncryptedMessage(
            message_id=message['id'],
            from_user=message['from_user'],
            to_user=message['to_user'],
            encrypted_content=message['encrypted_content'],
            encryption_key=message['encryption_key'],
            iv=message['iv'],
            algorithm=message['algorithm'],
            message_type=message['message_type'],
            attachments=json.loads(message['attachments']),
            created_at=message['created_at'],
            read=message['read']
        )
    
    async def decrypt_message(self, encrypted_message: EncryptedMessage,
                            private_key: str) -> Optional[str]:
        """Decrypt an encrypted message."""
        try:
            encrypted_data = {
                'ciphertext': encrypted_message.encrypted_content,
                'encrypted_key': encrypted_message.encryption_key,
                'iv': encrypted_message.iv,
                'algorithm': encrypted_message.algorithm
            }
            
            decrypted = self.crypto.decrypt_message(encrypted_data, private_key)
            return decrypted
        except Exception as e:
            print(f"Decryption failed: {e}")
            return None
    
    async def get_conversation(self, user1: str, user2: str,
                             limit: int = 50,
                             offset: int = 0) -> List[EncryptedMessage]:
        """Get conversation between two users."""
        messages = await self.db.fetch(
            """SELECT id, from_user, to_user, encrypted_content, encryption_key,
                      iv, algorithm, message_type, attachments, created_at, read
            FROM direct_messages 
            WHERE (from_user = $1 AND to_user = $2)
               OR (from_user = $2 AND to_user = $1)
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4""",
            user1, user2, limit, offset
        )
        
        return [
            EncryptedMessage(
                message_id=msg['id'],
                from_user=msg['from_user'],
                to_user=msg['to_user'],
                encrypted_content=msg['encrypted_content'],
                encryption_key=msg['encryption_key'],
                iv=msg['iv'],
                algorithm=msg['algorithm'],
                message_type=msg['message_type'],
                attachments=json.loads(msg['attachments']),
                created_at=msg['created_at'],
                read=msg['read']
            )
            for msg in messages
        ]
    
    async def mark_as_read(self, message_id: str, user_address: str) -> bool:
        """Mark message as read by recipient."""
        result = await self.db.execute(
            """UPDATE direct_messages 
            SET read = TRUE 
            WHERE id = $1 AND to_user = $2""",
            message_id, user_address
        )
        
        return "UPDATE 1" in result
    
    async def get_unread_count(self, user_address: str) -> int:
        """Get count of unread messages for user."""
        count = await self.db.fetchval(
            "SELECT COUNT(*) FROM direct_messages WHERE to_user = $1 AND read = FALSE",
            user_address
        )
        
        return count or 0
    
    async def _get_public_key(self, user_address: str) -> Optional[str]:
        """Get public key for a user."""
        if '@' not in user_address:
            return None
        
        username, domain = user_address.split('@', 1)
        
        key = await self.db.fetchval(
            "SELECT public_key FROM federated_users WHERE username = $1 AND domain = $2",
            username, domain
        )
        
        return key
