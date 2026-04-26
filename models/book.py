"""Book model with ISBN support and metadata."""

from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.author import Author
    from models.genre import Genre
    from models.user import User
    from models.review import Review
    from models.reading_progress import ReadingProgress


class BookFormat(str, PyEnum):
    """Book format enumeration."""
    HARDCOVER = "hardcover"
    PAPERBACK = "paperback"
    EBOOK = "ebook"
    AUDIOBOOK = "audiobook"


class BookStatus(str, PyEnum):
    """Reading status enumeration."""
    WANT_TO_READ = "want_to_read"
    READING = "reading"
    READ = "read"
    DNF = "did_not_finish"


class Book(BaseModel):
    """Book model with comprehensive metadata."""
    
    __tablename__ = "books"
    
    # Identification
    isbn_10 = Column(String(10), unique=True, nullable=True, index=True)
    isbn_13 = Column(String(13), unique=True, nullable=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    subtitle = Column(String(500), nullable=True)
    
    # Relationships
    author_id = Column(String(36), ForeignKey("authors.id"), nullable=False, index=True)
    author: "Author" = relationship("Author", back_populates="books")
    
    genre_id = Column(String(36), ForeignKey("genres.id"), nullable=True, index=True)
    genre: "Genre" = relationship("Genre", back_populates="books")
    
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    owner: "User" = relationship("User", back_populates="books")
    
    # Metadata
    description = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    publisher = Column(String(200), nullable=True)
    published_date = Column(Date, nullable=True)
    language = Column(String(10), default="en", nullable=False)
    format = Column(Enum(BookFormat), default=BookFormat.PAPERBACK, nullable=False)
    
    # Media
    cover_image_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    
    # User data
    status = Column(Enum(BookStatus), default=BookStatus.WANT_TO_READ, nullable=False)
    personal_rating = Column(Numeric(2, 1), nullable=True)
    notes = Column(Text, nullable=True)
    date_acquired = Column(Date, nullable=True)
    purchase_price = Column(Numeric(10, 2), nullable=True)
    
    # Relationships to other models
    reviews: List["Review"] = relationship("Review", back_populates="book", lazy="dynamic", cascade="all, delete-orphan")
    reading_progress: List["ReadingProgress"] = relationship("ReadingProgress", back_populates="book", lazy="dynamic", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Book(id={self.id}, title={self.title}, isbn={self.isbn_13})>"
