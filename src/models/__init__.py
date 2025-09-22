"""
MetaFederate Models Module
Data models and business logic for social interactions.

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

from .user import UserManager, FederatedUser
from .social import SocialGraph, RelationshipStatus
from .content import ContentManager, ContentType, PrivacyLevel
from .messaging import MessageManager, EncryptedMessage
from .groups import GroupManager, Group, GroupMembership
from .social_interactions import SocialInteractions, InteractionType

__all__ = [
    'UserManager', 'FederatedUser',
    'SocialGraph', 'RelationshipStatus',
    'ContentManager', 'ContentType', 'PrivacyLevel',
    'MessageManager', 'EncryptedMessage',
    'GroupManager', 'Group', 'GroupMembership',
    'SocialInteractions', 'InteractionType'
]
