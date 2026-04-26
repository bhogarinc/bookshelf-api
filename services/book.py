"""Book business logic service."""

import logging
from typing import List, Optional, Tuple

from models.book import Book, BookStatus
from repositories.author import AuthorRepository
from repositories.book import BookRepository
from schemas.book import BookCreate, BookUpdate, ISBNLookupResponse
from services.isbn_lookup import ISBNLookupService

logger = logging.getLogger(__name__)


class BookService:
    """Book business logic service."""
    
    def __init__(
        self,
        book_repo: BookRepository,
        author_repo: AuthorRepository,
        isbn_service: ISBNLookupService
    ):
        self.book_repo = book_repo
        self.author_repo = author_repo
        self.isbn_service = isbn_service
    
    async def create_book(self, user_id: str, book_data: BookCreate) -> Book:
        """Create new book with validation."""
        # Verify author exists
        author = await self.author_repo.get_by_id(book_data.author_id)
        if not author:
            raise ValueError(f"Author not found: {book_data.author_id}")
        
        # Check for duplicate ISBN
        if book_data.isbn_13:
            existing = await self.book_repo.get_by_isbn(book_data.isbn_13)
            if existing and str(existing.owner_id) == user_id:
                raise ValueError("Book with this ISBN already in your collection")
        
        book_dict = book_data.model_dump()
        book_dict["owner_id"] = user_id
        
        book = await self.book_repo.create(**book_dict)
        logger.info(f"Book created: {book.title} for user {user_id}")
        return book
    
    async def update_book(
        self,
        book_id: str,
        user_id: str,
        book_data: BookUpdate
    ) -> Optional[Book]:
        """Update book with ownership verification."""
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            return None
        
        if str(book.owner_id) != user_id:
            raise PermissionError("Not authorized to update this book")
        
        update_dict = book_data.model_dump(exclude_unset=True)
        updated = await self.book_repo.update(book_id, **update_dict)
        
        logger.info(f"Book updated: {book_id}")
        return updated
    
    async def delete_book(self, book_id: str, user_id: str) -> bool:
        """Delete book with ownership verification."""
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            return False
        
        if str(book.owner_id) != user_id:
            raise PermissionError("Not authorized to delete this book")
        
        return await self.book_repo.delete(book_id)
    
    async def get_user_library(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        **filters
    ) -> Tuple[List[Book], int]:
        """Get paginated library for user."""
        skip = (page - 1) * page_size
        return await self.book_repo.get_user_books(
            user_id=user_id,
            skip=skip,
            limit=page_size,
            **filters
        )
    
    async def lookup_isbn(self, isbn: str) -> Optional[ISBNLookupResponse]:
        """Lookup book by ISBN using external APIs."""
        # Validate ISBN
        cleaned_isbn = isbn.replace("-", "").replace(" ", "")
        if len(cleaned_isbn) not in [10, 13] or not cleaned_isbn.isdigit():
            raise ValueError("Invalid ISBN format")
        
        return await self.isbn_service.lookup(cleaned_isbn)
    
    async def get_reading_statistics(self, user_id: str) -> dict:
        """Get comprehensive reading statistics."""
        return await self.book_repo.get_statistics(user_id)
