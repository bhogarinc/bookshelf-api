"""User model and related schemas."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.book import Book
    from models.review import Review
    from models.wishlist import Wishlist
    from models.reading_progress import ReadingProgress


class User(BaseModel):
    """User account model."""
    
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    
    # Relationships
    books: List["Book"] = relationship("Book", back_populates="owner", lazy="dynamic")
    reviews: List["Review"] = relationship("Review", back_populates="user", lazy="dynamic")
    wishlists: List["Wishlist"] = relationship("Wishlist", back_populates="user", lazy="dynamic")
    reading_progress: List["ReadingProgress"] = relationship("ReadingProgress", back_populates="user", lazy="dynamic")
    
    @property
    def full_name(self) -> Optional[str]:
        """Return full name if available."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
