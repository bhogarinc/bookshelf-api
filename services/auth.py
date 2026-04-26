"""Authentication and authorization service."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import settings
from models.user import User
from repositories.user import UserRepository
from schemas.user import UserCreate

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service handling JWT and password operations."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Hash password."""
        return pwd_context.hash(password)
    
    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    
    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"Token decode error: {e}")
            return None
    
    async def authenticate_user(self, email_or_username: str, password: str) -> Optional[User]:
        """Authenticate user with credentials."""
        user = await self.user_repo.get_by_email_or_username(email_or_username)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    async def register_user(self, user_data: UserCreate) -> Tuple[User, str, str]:
        """Register new user and return tokens."""
        # Check existing
        if await self.user_repo.is_email_taken(user_data.email):
            raise ValueError("Email already registered")
        
        if await self.user_repo.is_username_taken(user_data.username):
            raise ValueError("Username already taken")
        
        # Create user
        hashed_password = self.hash_password(user_data.password)
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["hashed_password"] = hashed_password
        
        user = await self.user_repo.create(**user_dict)
        
        # Generate tokens
        access_token = self.create_access_token(str(user.id))
        refresh_token = self.create_refresh_token(str(user.id))
        
        logger.info(f"User registered: {user.email}")
        return user, access_token, refresh_token
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create new access token from refresh token."""
        payload = self.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        user = await self.user_repo.get_by_id(user_id)
        
        if not user or not user.is_active:
            return None
        
        return self.create_access_token(user_id)
