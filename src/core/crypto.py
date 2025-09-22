"""
MetaFederate Cryptography Module
End-to-end encryption and cryptographic operations for secure federation.

Key Responsibilities:
- Message encryption/decryption
- Key pair generation and management
- Digital signatures and verification
- Password hashing and verification

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

import base64
import os
from typing import Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import bcrypt

class Crypto:
    """Cryptography operations for MetaFederate."""
    
    @staticmethod
    def generate_key_pair() -> Dict[str, str]:
        """Generate RSA key pair for user encryption."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return {
            'private_key': private_pem,
            'public_key': public_pem
        }
    
    @staticmethod
    def encrypt_message(plaintext: str, public_key_pem: str) -> Dict[str, Any]:
        """Encrypt message using recipient's public key."""
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
        
        # Generate symmetric key for this message
        symmetric_key = Fernet.generate_key()
        fernet = Fernet(symmetric_key)
        
        # Encrypt content with symmetric key
        ciphertext = fernet.encrypt(plaintext.encode('utf-8'))
        
        # Encrypt symmetric key with RSA
        encrypted_key = public_key.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'encrypted_key': base64.b64encode(encrypted_key).decode('utf-8'),
            'algorithm': 'RSA-OAEP+AES256',
            'version': '1.0'
        }
    
    @staticmethod
    def decrypt_message(encrypted_data: Dict[str, Any], private_key_pem: str) -> str:
        """Decrypt message using recipient's private key."""
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        
        # Decrypt symmetric key
        encrypted_key = base64.b64decode(encrypted_data['encrypted_key'])
        symmetric_key = private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Decrypt message content
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        fernet = Fernet(symmetric_key)
        plaintext = fernet.decrypt(ciphertext)
        
        return plaintext.decode('utf-8')
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hashed password."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    @staticmethod
    def generate_signature(data: str, private_key_pem: str) -> str:
        """Generate digital signature for data."""
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        
        signature = private_key.sign(
            data.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode('utf-8')
    
    @staticmethod
    def verify_signature(data: str, signature: str, public_key_pem: str) -> bool:
        """Verify digital signature."""
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
        
        signature_bytes = base64.b64decode(signature)
        
        try:
            public_key.verify(
                signature_bytes,
                data.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
