"""
MetaFederate Configuration Module
Centralized configuration management for the federation protocol.

Key Responsibilities:
- Environment variable handling
- Configuration validation
- Default value management
- Runtime configuration updates

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration management for MetaFederate."""
    
    _config: Dict[str, Any] = {
        'database': {
            'url': os.getenv('MF_DATABASE_URL', 'postgresql://user:pass@localhost/metafederate'),
            'pool_size': int(os.getenv('MF_DB_POOL_SIZE', '20')),
            'max_overflow': int(os.getenv('MF_DB_MAX_OVERFLOW', '10')),
            'timeout': int(os.getenv('MF_DB_TIMEOUT', '30'))
        },
        'server': {
            'domain': os.getenv('MF_DOMAIN', 'localhost'),
            'port': int(os.getenv('MF_PORT', '8000')),
            'debug': os.getenv('MF_DEBUG', 'false').lower() == 'true',
            'host': os.getenv('MF_HOST', '0.0.0.0')
        },
        'federation': {
            'timeout': int(os.getenv('MF_FEDERATION_TIMEOUT', '10')),
            'max_message_size': int(os.getenv('MF_MAX_MESSAGE_SIZE', '10485760')),
            'retry_attempts': int(os.getenv('MF_RETRY_ATTEMPTS', '3')),
            'retry_delay': int(os.getenv('MF_RETRY_DELAY', '5'))
        },
        'security': {
            'jwt_secret': os.getenv('MF_JWT_SECRET', 'change-this-in-production'),
            'encryption_algorithm': os.getenv('MF_ENCRYPTION_ALGO', 'aes-256-gcm'),
            'rate_limit_requests': int(os.getenv('MF_RATE_LIMIT_REQUESTS', '100')),
            'rate_limit_period': int(os.getenv('MF_RATE_LIMIT_PERIOD', '300'))
        },
        'logging': {
            'level': os.getenv('MF_LOG_LEVEL', 'INFO'),
            'file': os.getenv('MF_LOG_FILE', 'metafederate.log'),
            'max_size': int(os.getenv('MF_LOG_MAX_SIZE', '10485760')),
            'backup_count': int(os.getenv('MF_LOG_BACKUP_COUNT', '5'))
        }
    }
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = cls._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set configuration value."""
        keys = key.split('.')
        config = cls._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @classmethod
    def load_from_file(cls, file_path: str) -> None:
        """Load configuration from JSON file."""
        try:
            with open(file_path, 'r') as f:
                file_config = json.load(f)
            cls._config.update(file_config)
        except FileNotFoundError:
            raise Exception(f"Configuration file not found: {file_path}")
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON in configuration file: {file_path}")
    
    @classmethod
    def save_to_file(cls, file_path: str) -> None:
        """Save configuration to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(cls._config, f, indent=2)
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration values."""
        required_keys = [
            'database.url',
            'server.domain',
            'security.jwt_secret'
        ]
        
        for key in required_keys:
            if cls.get(key) is None:
                raise ValueError(f"Missing required configuration: {key}")
        
        # Validate database URL format
        db_url = cls.get('database.url')
        if not (db_url.startswith('postgresql://') or db_url.startswith('mysql://')):
            raise ValueError("Invalid database URL format")
        
        return True
