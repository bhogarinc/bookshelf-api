"""Book management routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from config.logging_config import get_logger
from models.book import BookStatus
from models.user import User
from repositories.author import AuthorRepository
from repositories.book import BookRepository
from schemas.book import BookCreate, BookListResponse, BookResponse, BookUpdate, ISBNLookupResponse
from services.book import BookService
from services.isbn_lookup import ISBNLookupService

logger = get_logger(__name__)
router = APIRouter(prefix="/books", tags=["Books"])


def get_book_service(session: AsyncSession = Depends(get_db_session)) -> BookService:
    """Dependency for book service."""
    return BookService(
        book_repo=BookRepository(session),
        author_repo=AuthorRepository(session),
        isbn_service=ISBNLookupService()
    )


@router.get("", response_model=BookListResponse)
async def list_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[BookStatus] = None,
    genre_id: Optional[str] = None,
    author_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_desc: bool = True,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends(get_book_service)
):
    """List user's book collection with filtering."""
    books, total = await service.get_user_library(
        user_id=str(current_user.id),
        page=page,
        page_size=page_size,
        status=status,
        genre_id=genre_id,
        author_id=author_id,
        search=search,
        sort_by=sort_by,
        sort_desc=sort_desc
    )
    
    pages = (total + page_size - 1) // page_size
    
    return BookListResponse(
        items=[BookResponse.model_validate(b) for b in books],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_data: BookCreate,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends(get_book_service)
):
    """Add new book to collection."""
    try:
        book = await service.create_book(str(current_user.id), book_data)
        return BookResponse.model_validate(book)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/isbn/{isbn}", response_model=ISBNLookupResponse)
async def lookup_isbn(
    isbn: str,
    _: User = Depends(get_current_user),
    service: BookService = Depends(get_book_service)
):
    """Lookup book by ISBN."""
    result = await service.lookup_isbn(isbn)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ISBN not found"
        )
    return result


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends(get_book_service)
):
    """Get single book by ID."""
    book = await service.book_repo.get_by_id(book_id)
    if not book or str(book.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return BookResponse.model_validate(book)


@router.patch("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: str,
    book_data: BookUpdate,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends(get_book_service)
):
    """Update book details."""
    try:
        book = await service.update_book(book_id, str(current_user.id), book_data)
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        return BookResponse.model_validate(book)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: str,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends(get_book_service)
):
    """Delete book from collection."""
    try:
        deleted = await service.delete_book(book_id, str(current_user.id))
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/statistics/dashboard")
async def get_statistics(
    current_user: User = Depends(get_current_user),
    service: BookService = Depends(get_book_service)
):
    """Get reading statistics dashboard data."""
    stats = await service.get_reading_statistics(str(current_user.id))
    return stats
