"""
MetaFederate Middleware
Authentication, rate limiting, and validation middleware.

Key Responsibilities:
- JWT authentication
- Rate limiting enforcement
- Request validation
- CORS handling

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

import time
from aiohttp import web
import jwt
from typing import Dict, Any, Optional
from functools import wraps
from ..core.config import Config
from ..core.database import Database

class AuthMiddleware:
    """JWT authentication middleware."""
    
    def __init__(self):
        self.secret = Config.get('security.jwt_secret')
        self.algorithm = 'HS256'
    
    @staticmethod
    def generate_token(user_id: str, username: str) -> str:
        """Generate JWT token for user."""
        payload = {
            'user_id': user_id,
            'username': username,
            'iat': time.time(),
            'exp': time.time() + Config.get('security.jwt_expire', 3600)
        }
        return jwt.encode(payload, Config.get('security.jwt_secret'), algorithm='HS256')
    
    async def middleware(self, app, handler):
        """Authentication middleware."""
        async def middleware_handler(request):
            # Skip auth for public endpoints
            if request.path in ['/api/v1/users', '/api/v1/users/login', 
                              '/.well-known/webfinger', '/.well-known/nodeinfo']:
                return await handler(request)
            
            # Check for Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return web.json_response(
                    {'error': 'Authentication required'}, status=401
                )
            
            token = auth_header[7:]
            try:
                payload = jwt.decode(
                    token, 
                    self.secret, 
                    algorithms=[self.algorithm]
                )
                request['user_id'] = payload['user_id']
                request['username'] = payload['username']
            except jwt.ExpiredSignatureError:
                return web.json_response(
                    {'error': 'Token expired'}, status=401
                )
            except jwt.InvalidTokenError:
                return web.json_response(
                    {'error': 'Invalid token'}, status=401
                )
            
            return await handler(request)
        
        return middleware_handler

class RateLimitMiddleware:
    """Rate limiting middleware."""
    
    def __init__(self):
        self.redis = None  # Would be initialized with Redis connection
        self.rate_limit = Config.get('security.rate_limit_requests', 100)
        self.rate_period = Config.get('security.rate_limit_period', 300)
    
    async def middleware(self, app, handler):
        """Rate limiting middleware."""
        async def middleware_handler(request):
            # Skip rate limiting for federation endpoints
            if request.path.startswith('/federation/'):
                return await handler(request)
            
            client_ip = request.remote
            user_id = request.get('user_id', 'anonymous')
            
            # Use user_id for authenticated users, IP for anonymous
            identifier = user_id if user_id != 'anonymous' else client_ip
            
            current = int(time.time())
            window_start = current - self.rate_period
            
            # This would use Redis in production
            # For now, we'll use a simple in-memory approach
            key = f"ratelimit:{identifier}"
            
            # Check if rate limit exceeded
            request_count = await self.get_request_count(key, window_start)
            if request_count >= self.rate_limit:
                return web.json_response(
                    {'error': 'Rate limit exceeded'}, status=429
                )
            
            # Increment request count
            await self.increment_request_count(key, current)
            
            return await handler(request)
        
        return middleware_handler
    
    async def get_request_count(self, key: str, window_start: int) -> int:
        """Get request count for time window."""
        # In production, this would use Redis ZCOUNT
        return 0  # Placeholder
    
    async def increment_request_count(self, key: str, timestamp: int) -> None:
        """Increment request count."""
        # In production, this would use Redis ZADD
        pass

class ValidationMiddleware:
    """Request validation middleware."""
    
    async def middleware(self, app, handler):
        """Validation middleware."""
        async def middleware_handler(request):
            # Validate JSON content type for POST/PUT requests
            if request.method in ['POST', 'PUT']:
                content_type = request.headers.get('Content-Type', '')
                if not content_type.startswith('application/json'):
                    return web.json_response(
                        {'error': 'Content-Type must be application/json'}, status=400
                    )
            
            return await handler(request)
        
        return middleware_handler

# CORS middleware setup
def setup_cors(app: web.Application) -> None:
    """Setup CORS for the application."""
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            if request.method == 'OPTIONS':
                response = web.Response()
            else:
                response = await handler(request)
            
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            
            return response
        
        return middleware_handler
    
    app.middlewares.append(cors_middleware)
