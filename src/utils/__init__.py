"""
MetaFederate Utilities Module
Protocol compatibility and utility functions.

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

from .activitypub import ActivityPubAdapter
from .webfinger import WebFingerService
from .diaspora import DiasporaAdapter
from .helpers import generate_id, validate_domain, sanitize_content

__all__ = [
    'ActivityPubAdapter',
    'WebFingerService',
    'DiasporaAdapter',
    'generate_id',
    'validate_domain',
    'sanitize_content'
]
