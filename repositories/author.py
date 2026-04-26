"""Author repository."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.author import Author
from repositories.base import BaseRepository


class AuthorRepository(BaseRepository[Author]):
    """Author repository operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Author, session)
    
    async def get_by_name(self, name: str) -> Optional[Author]:
        """Get author by exact name match."""
        result = await self.session.execute(
            select(Author).where(Author.name == name)
        )
        return result.scalar_one_or_none()
    
    async def search_by_name(self, query: str, limit: int = 10) -> List[Author]:
        """Search authors by name (partial match)."""
        result = await self.session.execute(
            select(Author)
            .where(Author.name.ilike(f"%{query}%"))
            .limit(limit)
        )
        return list(result.scalars().all())
