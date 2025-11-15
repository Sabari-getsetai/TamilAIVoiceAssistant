"""Authentication Service - JWT and Password Management

This service handles:
- Password hashing and verification
- JWT token creation and validation
- Token lifecycle management
- User authentication validation

Replaces: backend.api.helper.AuthHelper (JWT/password functions)
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
import bcrypt
from jose import jwt, JWTError
from fastapi import HTTPException, status

from backend.utils.base_service import BaseService
from backend.settings import settings


class AuthenticationService(BaseService):
    """Service for authentication operations including JWT and password management"""

    def __init__(self):
        super().__init__()
        self.service_name = "AuthenticationService"

    # Password operations
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with secure salt generation

        Args:
            password: Plain text password to hash

        Returns:
            Hashed password string safe for database storage

        Raises:
            ValueError: If password is empty or invalid
        """
        if not password or not password.strip():
            raise ValueError("Password cannot be empty")

        try:
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Password hashing failed: {str(e)}")
            raise ValueError("Failed to hash password")

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against stored hash

        Args:
            password: Plain text password to verify
            hashed: Stored password hash from database

        Returns:
            True if password matches hash, False otherwise
        """
        if not password or not hashed:
            return False

        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            self.logger.warning(f"Password verification failed: {str(e)}")
            return False

    # JWT token operations
    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token for user authentication

        Args:
            user_id: User ID to encode in token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT access token

        Raises:
            ValueError: If user_id is invalid
        """
        if not user_id or not user_id.strip():
            raise ValueError("User ID is required for token creation")

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        }

        try:
            return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        except Exception as e:
            self.logger.error(f"Access token creation failed for user {user_id}: {str(e)}")
            raise ValueError("Failed to create access token")

    def create_refresh_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT refresh token for token renewal

        Args:
            user_id: User ID to encode in token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT refresh token with unique identifier

        Raises:
            ValueError: If user_id is invalid
        """
        if not user_id or not user_id.strip():
            raise ValueError("User ID is required for token creation")

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "jti": str(uuid4())  # Unique token ID for refresh tokens
        }

        try:
            return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        except Exception as e:
            self.logger.error(f"Refresh token creation failed for user {user_id}: {str(e)}")
            raise ValueError("Failed to create refresh token")

    def verify_token(self, token: str, token_type: str = "access") -> Optional[str]:
        """Verify JWT token and extract user ID

        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")

        Returns:
            User ID if token is valid, None if invalid but not expired

        Raises:
            HTTPException: If token is expired or malformed (for HTTP context)
        """
        if not token or not token.strip():
            return None

        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            token_type_claim: str = payload.get("type")

            if user_id is None or token_type_claim != token_type:
                self.logger.warning(f"Invalid token claims: user_id={user_id}, type={token_type_claim}")
                return None

            return user_id

        except jwt.ExpiredSignatureError:
            self.logger.info(f"Token expired for type: {token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            self.logger.warning(f"JWT validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            self.logger.error(f"Unexpected token verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def verify_token_silent(self, token: str, token_type: str = "access") -> Optional[str]:
        """Verify JWT token without raising HTTP exceptions

        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")

        Returns:
            User ID if token is valid, None if invalid or expired

        Note:
            This method is useful for optional authentication scenarios
            where you don't want to raise exceptions for invalid tokens
        """
        if not token or not token.strip():
            return None

        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            token_type_claim: str = payload.get("type")

            if user_id is None or token_type_claim != token_type:
                return None

            return user_id

        except (jwt.ExpiredSignatureError, JWTError, Exception):
            return None

    def extract_token_claims(self, token: str) -> Optional[dict]:
        """Extract all claims from JWT token without validation

        Args:
            token: JWT token to decode

        Returns:
            Dictionary of token claims if decodable, None otherwise

        Note:
            This method does not verify token signature or expiration.
            Use only for extracting metadata from tokens.
        """
        try:
            # Decode without verification for claim extraction
            return jwt.get_unverified_claims(token)
        except Exception:
            return None

    def is_token_expired(self, token: str) -> bool:
        """Check if JWT token is expired without full validation

        Args:
            token: JWT token to check

        Returns:
            True if token is expired, False if valid or unparseable
        """
        claims = self.extract_token_claims(token)
        if not claims or 'exp' not in claims:
            return True

        try:
            exp_timestamp = claims['exp']
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            return datetime.utcnow() > exp_datetime
        except Exception:
            return True