"""
MetaFederate REST API
RESTful API endpoints for federated social interactions.

Key Responsibilities:
- User management endpoints
- Content creation and retrieval
- Social interaction endpoints
- Federation protocol compliance

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

from aiohttp import web
import json
from typing import Dict, Any, Optional
from datetime import datetime
from ..core.config import Config
from ..core.database import Database
from ..models import UserManager, ContentManager, SocialInteractions, SocialGraph
from .middleware import AuthMiddleware, RateLimitMiddleware

class RESTAPI:
    """REST API server for MetaFederate."""
    
    def __init__(self, db: Database):
        self.db = db
        self.app = web.Application(
            middlewares=[
                AuthMiddleware().middleware,
                RateLimitMiddleware().middleware
            ]
        )
        self.setup_routes()
    
    def setup_routes(self) -> None:
        """Setup all API routes."""
        # User routes
        self.app.router.add_post('/api/v1/users', self.create_user)
        self.app.router.add_get('/api/v1/users/{user_id}', self.get_user)
        self.app.router.add_post('/api/v1/users/login', self.login_user)
        
        # Content routes
        self.app.router.add_post('/api/v1/content', self.create_content)
        self.app.router.add_get('/api/v1/content/{content_id}', self.get_content)
        self.app.router.add_get('/api/v1/timeline', self.get_timeline)
        
        # Social interaction routes
        self.app.router.add_post('/api/v1/interactions/like', self.like_content)
        self.app.router.add_post('/api/v1/interactions/comment', self.comment_content)
        self.app.router.add_post('/api/v1/interactions/repost', self.repost_content)
        
        # Federation routes
        self.app.router.add_post('/federation/inbox', self.federation_inbox)
        self.app.router.add_get('/.well-known/webfinger', self.webfinger)
        self.app.router.add_get('/.well-known/nodeinfo', self.nodeinfo)
    
    async def create_user(self, request: web.Request) -> web.Response:
        """Create a new user."""
        try:
            data = await request.json()
            user_manager = UserManager(self.db)
            
            user = await user_manager.create_user(
                username=data['username'],
                password=data['password'],
                domain=Config.get('server.domain'),
                display_name=data.get('display_name'),
                bio=data.get('bio'),
                avatar_url=data.get('avatar_url')
            )
            
            return web.json_response({
                'status': 'success',
                'user': user.to_dict()
            }, status=201)
            
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    async def login_user(self, request: web.Request) -> web.Response:
        """Authenticate user and return JWT token."""
        try:
            data = await request.json()
            user_manager = UserManager(self.db)
            
            user = await user_manager.authenticate_user(
                username=data['username'],
                password=data['password'],
                domain=Config.get('server.domain')
            )
            
            if user:
                # Generate JWT token
                token = AuthMiddleware.generate_token(user.user_id, user.username)
                
                return web.json_response({
                    'status': 'success',
                    'token': token,
                    'user': user.to_dict()
                })
            else:
                return web.json_response({
                    'status': 'error',
                    'message': 'Invalid credentials'
                }, status=401)
                
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    async def create_content(self, request: web.Request) -> web.Response:
        """Create new content."""
        try:
            data = await request.json()
            user_id = request['user_id']
            content_manager = ContentManager(self.db)
            
            content = await content_manager.create_content(
                author=f"{data['username']}@{Config.get('server.domain')}",
                content=data['content'],
                content_type=data.get('content_type', 'post'),
                privacy=data.get('privacy', 'public'),
                media_urls=data.get('media_urls', []),
                in_reply_to=data.get('in_reply_to')
            )
            
            return web.json_response({
                'status': 'success',
                'content': content
            }, status=201)
            
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    async def like_content(self, request: web.Request) -> web.Response:
        """Like content across platforms."""
        try:
            data = await request.json()
            user_id = request['user_id']
            interactions = SocialInteractions(self.db)
            
            result = await interactions.like_content(
                user_address=data['user_address'],
                content_id=data['content_id'],
                reaction=data.get('reaction', '❤️')
            )
            
            return web.json_response({
                'status': 'success',
                'result': result
            })
            
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    async def federation_inbox(self, request: web.Request) -> web.Response:
        """Receive federation activities."""
        try:
            activity = await request.json()
            # Process federation activity
            # This would be handled by the federation module
            
            return web.json_response({
                'status': 'accepted'
            }, status=202)
            
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    async def webfinger(self, request: web.Request) -> web.Response:
        """WebFinger protocol endpoint."""
        resource = request.query.get('resource')
        if resource and resource.startswith('acct:'):
            username = resource.split('acct:')[1].split('@')[0]
            domain = resource.split('@')[1]
            
            if domain == Config.get('server.domain'):
                return web.json_response({
                    'subject': resource,
                    'links': [
                        {
                            'rel': 'self',
                            'type': 'application/activity+json',
                            'href': f"https://{domain}/users/{username}"
                        }
                    ]
                })
        
        return web.json_response({'error': 'Not found'}, status=404)
    
    async def nodeinfo(self, request: web.Request) -> web.Response:
        """NodeInfo protocol endpoint."""
        return web.json_response({
            'links': [
                {
                    'rel': 'http://nodeinfo.diaspora.software/ns/schema/2.1',
                    'href': f"https://{Config.get('server.domain')}/nodeinfo/2.1"
                }
            ]
        })

def create_app(db: Database) -> web.Application:
    """Create and configure the web application."""
    api = RESTAPI(db)
    return api.app
