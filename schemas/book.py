"""Book Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator

from models.book import BookFormat, BookStatus


class AuthorBrief(BaseModel):
    """Brief author info."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str


class GenreBrief(BaseModel):
    """Brief genre info."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str


class BookBase(BaseModel):
    """Base book schema."""
    isbn_10: Optional[str] = Field(None, max_length=10)
    isbn_13: Optional[str] = Field(None, max_length=13)
    title: str = Field(..., min_length=1, max_length=500)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    page_count: Optional[int] = Field(None, gt=0)
    publisher: Optional[str] = Field(None, max_length=200)
    published_date: Optional[date] = None
    language: str = Field(default="en", max_length=10)
    format: BookFormat = BookFormat.PAPERBACK
    cover_image_url: Optional[str] = Field(None, max_length=500)
    status: BookStatus = BookStatus.WANT_TO_READ
    personal_rating: Optional[Decimal] = Field(None, ge=1, le=5, decimal_places=1)
    notes: Optional[str] = None
    purchase_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    
    @field_validator('isbn_10')
    @classmethod
    def validate_isbn10(cls, v: Optional[str]) -> Optional[str]:
        if v and (not v.isdigit() or len(v) != 10):
            raise ValueError("ISBN-10 must be 10 digits")
        return v
    
    @field_validator('isbn_13')
    @classmethod
    def validate_isbn13(cls, v: Optional[str]) -> Optional[str]:
        if v and (not v.isdigit() or len(v) != 13):
            raise ValueError("ISBN-13 must be 13 digits")
        return v


class BookCreate(BookBase):
    """Book creation schema."""
    author_id: str
    genre_id: Optional[str] = None


class BookUpdate(BaseModel):
    """Book update schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    page_count: Optional[int] = Field(None, gt=0)
    publisher: Optional[str] = Field(None, max_length=200)
    published_date: Optional[date] = None
    language: Optional[str] = Field(None, max_length=10)
    format: Optional[BookFormat] = None
    status: Optional[BookStatus] = None
    personal_rating: Optional[Decimal] = Field(None, ge=1, le=5, decimal_places=1)
    notes: Optional[str] = None
    genre_id: Optional[str] = None


class BookResponse(BookBase):
    """Book response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    author: AuthorBrief
    genre: Optional[GenreBrief]
    owner_id: str
    created_at: datetime
    updated_at: datetime


class BookListResponse(BaseModel):
    """Paginated book list response."""
    items: List[BookResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ISBNLookupResponse(BaseModel):
    """ISBN lookup response."""
    isbn: str
    title: str
    subtitle: Optional[str]
    authors: List[str]
    publisher: Optional[str]
    published_date: Optional[str]
    description: Optional[str]
    page_count: Optional[int]
    categories: List[str]
    cover_image_url: Optional[str]
    language: Optional[str]
