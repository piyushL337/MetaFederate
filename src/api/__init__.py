"""
MetaFederate API Module
REST API endpoints and WebSocket handlers for federated social protocol.

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

from .rest import RESTAPI, create_app
from .websocket import WebSocketManager
from .middleware import AuthMiddleware, RateLimitMiddleware, ValidationMiddleware

__all__ = [
    'RESTAPI',
    'create_app',
    'WebSocketManager',
    'AuthMiddleware',
    'RateLimitMiddleware',
    'ValidationMiddleware'
]
