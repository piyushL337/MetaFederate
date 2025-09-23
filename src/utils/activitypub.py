"""
MetaFederate ActivityPub Adapter
ActivityPub protocol compatibility layer.

Key Responsibilities:
- ActivityPub message conversion
- Protocol compliance
- Interoperability with other platforms

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

class ActivityPubAdapter:
    """ActivityPub protocol adapter for interoperability."""
    
    @staticmethod
    def create_note(actor: str, content: str, 
                   to: Optional[List[str]] = None,
                   cc: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create ActivityPub Note object."""
        return {
            '@context': 'https://www.w3.org/ns/activitystreams',
            'type': 'Note',
            'id': f"{actor}/notes/{int(datetime.now().timestamp())}",
            'attributedTo': actor,
            'content': content,
            'to': to or ['https://www.w3.org/ns/activitystreams#Public'],
            'cc': cc or [],
            'published': datetime.utcnow().isoformat() + 'Z'
        }
    
    @staticmethod
    def create_activity(actor: str, activity_type: str, 
                       object: Dict[str, Any]) -> Dict[str, Any]:
        """Create ActivityPub Activity."""
        return {
            '@context': 'https://www.w3.org/ns/activitystreams',
            'type': activity_type,
            'id': f"{actor}/activities/{int(datetime.now().timestamp())}",
            'actor': actor,
            'object': object,
            'published': datetime.utcnow().isoformat() + 'Z'
        }
    
    @staticmethod
    def convert_to_activitypub(content: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MetaFederate content to ActivityPub format."""
        if content['content_type'] == 'post':
            return ActivityPubAdapter.create_note(
                actor=content['author'],
                content=content['content'],
                to=[f"https://{content['author'].split('@')[1]}/followers"]
            )
        return content
    
    @staticmethod
    def convert_from_activitypub(activity: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ActivityPub activity to MetaFederate format."""
        if activity['type'] == 'Create' and activity['object']['type'] == 'Note':
            note = activity['object']
            return {
                'id': note['id'],
                'author': note['attributedTo'],
                'content': note['content'],
                'content_type': 'post',
                'privacy_level': 'public',
                'created_at': note['published']
            }
        return activity
