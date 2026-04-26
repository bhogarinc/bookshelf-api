"""Book repository with advanced filtering."""

from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.book import Book, BookStatus
from repositories.base import BaseRepository


class BookRepository(BaseRepository[Book]):
    """Book-specific repository operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Book, session)
    
    async def get_by_isbn(self, isbn: str) -> Optional[Book]:
        """Get book by ISBN-10 or ISBN-13."""
        result = await self.session.execute(
            select(Book).where(
                or_(Book.isbn_10 == isbn, Book.isbn_13 == isbn)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_books(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        status: Optional[BookStatus] = None,
        genre_id: Optional[str] = None,
        author_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> Tuple[List[Book], int]:
        """Get books for a user with filtering and pagination."""
        query = select(Book).where(Book.owner_id == user_id)
        count_query = select(func.count(Book.id)).where(Book.owner_id == user_id)
        
        # Apply filters
        if status:
            query = query.where(Book.status == status)
            count_query = count_query.where(Book.status == status)
        
        if genre_id:
            query = query.where(Book.genre_id == genre_id)
            count_query = count_query.where(Book.genre_id == genre_id)
        
        if author_id:
            query = query.where(Book.author_id == author_id)
            count_query = count_query.where(Book.author_id == author_id)
        
        if search:
            search_filter = or_(
                Book.title.ilike(f"%{search}%"),
                Book.subtitle.ilike(f"%{search}%"),
                Book.description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply sorting
        if hasattr(Book, sort_by):
            sort_column = getattr(Book, sort_by)
            query = query.order_by(
                sort_column.desc() if sort_desc else sort_column.asc()
            )
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def get_statistics(self, user_id: str) -> dict:
        """Get reading statistics for user."""
        # Status counts
        status_query = select(
            Book.status,
            func.count(Book.id).label('count'),
            func.coalesce(func.sum(Book.page_count), 0).label('pages')
        ).where(Book.owner_id == user_id).group_by(Book.status)
        
        status_result = await self.session.execute(status_query)
        status_counts = {
            row.status: {"count": row.count, "pages": row.pages}
            for row in status_result
        }
        
        # Total books and pages
        total_query = select(
            func.count(Book.id).label('total_books'),
            func.coalesce(func.sum(Book.page_count), 0).label('total_pages'),
            func.avg(Book.personal_rating).label('avg_rating')
        ).where(Book.owner_id == user_id)
        
        total_result = await self.session.execute(total_query)
        total_row = total_result.one()
        
        return {
            "total_books": total_row.total_books,
            "total_pages": int(total_row.total_pages),
            "average_rating": round(float(total_row.avg_rating or 0), 2),
            "by_status": status_counts
        }
