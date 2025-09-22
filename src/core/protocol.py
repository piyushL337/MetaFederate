"""
MetaFederate Protocol Handler
Main protocol implementation for handling cross-platform social activities.

Key Responsibilities:
- Activity validation and processing
- Cross-platform interaction handling
- Protocol compliance enforcement

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class ActivityType(Enum):
    """Supported activity types for federation protocol."""
    CREATE = "Create"
    UPDATE = "Update"
    DELETE = "Delete"
    FOLLOW = "Follow"
    BLOCK = "Block"
    LIKE = "Like"
    UNLIKE = "Undo"
    COMMENT = "Create"
    QUOTE = "Create"
    REPOST = "Announce"
    THREAD = "Create"
    MENTION = "Mention"
    REACTION = "Like"
    MESSAGE = "Message"

@dataclass
class FederatedUser:
    """Represents a federated user across platforms."""
    id: str
    username: str
    domain: str
    public_key: str
    following: List[str]
    followers: List[str]
    blocks: List[str]
    
    @property
    def full_address(self) -> str:
        return f"{self.username}@{self.domain}"

class MetaFederateProtocol:
    """Main protocol handler for MetaFederate activities."""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.logger = logging.getLogger(__name__)
        
    async def handle_activity(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming federation activities."""
        activity_type = activity.get('type')
        
        try:
            if activity_type == ActivityType.FOLLOW.value:
                return await self._handle_follow(activity)
            elif activity_type == ActivityType.BLOCK.value:
                return await self._handle_block(activity)
            elif activity_type == ActivityType.LIKE.value:
                return await self._handle_like(activity)
            elif activity_type == ActivityType.UNLIKE.value:
                return await self._handle_unlike(activity)
            elif activity_type == ActivityType.COMMENT.value:
                return await self._handle_comment(activity)
            elif activity_type == ActivityType.QUOTE.value:
                return await self._handle_quote(activity)
            elif activity_type == ActivityType.REPOST.value:
                return await self._handle_repost(activity)
            elif activity_type == ActivityType.THREAD.value:
                return await self._handle_thread(activity)
            elif activity_type == ActivityType.MESSAGE.value:
                return await self._handle_message(activity)
            else:
                return {"error": "Unsupported activity type"}
                
        except Exception as e:
            self.logger.error(f"Activity handling failed: {e}")
            return {"error": str(e)}
    
    async def _handle_follow(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle follow requests across platforms."""
        actor = activity['actor']
        target = activity['object']
        
        if await self._is_blocked(actor, target):
            return {"status": "blocked"}
        
        success = await self._add_follower(target, actor)
        return {"status": "success" if success else "failed"}
    
    async def _handle_like(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle likes across platforms."""
        actor = activity['actor']
        target_content = activity['object']
        reaction = activity.get('reaction', '❤️')
        
        if await self._can_interact(actor, target_content):
            like_id = await self._store_like(actor, target_content, reaction)
            return {"status": "liked", "like_id": like_id}
        return {"status": "not_allowed"}
    
    async def _handle_unlike(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unlikes across platforms."""
        actor = activity['actor']
        target_content = activity['object']
        
        success = await self._remove_like(actor, target_content)
        return {"status": "unliked" if success else "not_found"}
    
    async def _handle_comment(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle comments across platforms."""
        actor = activity['actor']
        comment_data = activity['object']
        target_content = comment_data.get('inReplyTo')
        
        if await self._can_interact(actor, target_content):
            comment_id = await self._store_comment(actor, target_content, comment_data)
            return {"status": "commented", "comment_id": comment_id}
        return {"status": "not_allowed"}
    
    async def _handle_quote(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quote posts across platforms."""
        actor = activity['actor']
        quote_data = activity['object']
        original_content = quote_data.get('quoteOf')
        
        if await self._can_interact(actor, original_content):
            quote_id = await self._store_quote(actor, original_content, quote_data)
            return {"status": "quoted", "quote_id": quote_id}
        return {"status": "not_allowed"}
    
    async def _handle_repost(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reposts across platforms."""
        actor = activity['actor']
        original_content = activity['object']
        repost_text = activity.get('content', '')
        
        if await self._can_interact(actor, original_content):
            repost_id = await self._store_repost(actor, original_content, repost_text)
            return {"status": "reposted", "repost_id": repost_id}
        return {"status": "not_allowed"}
    
    async def _handle_thread(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle thread creation and updates."""
        actor = activity['actor']
        thread_data = activity['object']
        
        if thread_data.get('type') == 'Thread':
            thread_id = await self._create_thread(actor, thread_data)
            return {"status": "thread_created", "thread_id": thread_id}
        return {"status": "invalid_thread_data"}
    
    async def _handle_message(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle encrypted cross-platform messaging."""
        message_data = activity['object']
        sender = message_data['from']
        receiver = message_data['to']
        
        if await self._is_blocked(sender, receiver):
            return {"status": "blocked"}
        
        message_id = await self._store_message(message_data)
        return {"status": "delivered", "message_id": message_id}
    
    async def _can_interact(self, actor: str, target_content: str) -> bool:
        """Check if actor can interact with target content."""
        # Implementation for interaction permissions
        return True
    
    async def _is_blocked(self, actor: str, target: str) -> bool:
        """Check if actor is blocked by target."""
        # Implementation for block checking
        return False
