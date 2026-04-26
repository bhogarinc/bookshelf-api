"""User repository with specific queries."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User-specific repository operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email_or_username(self, email_or_username: str) -> Optional[User]:
        """Get user by email or username."""
        result = await self.session.execute(
            select(User).where(
                (User.email == email_or_username) | (User.username == email_or_username)
            )
        )
        return result.scalar_one_or_none()
    
    async def is_email_taken(self, email: str, exclude_id: Optional[str] = None) -> bool:
        """Check if email is already registered."""
        query = select(User).where(User.email == email)
        if exclude_id:
            query = query.where(User.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def is_username_taken(self, username: str, exclude_id: Optional[str] = None) -> bool:
        """Check if username is already taken."""
        query = select(User).where(User.username == username)
        if exclude_id:
            query = query.where(User.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
