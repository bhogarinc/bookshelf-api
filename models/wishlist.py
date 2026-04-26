"""Wishlist model for books to acquire."""

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Numeric, Integer
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.book import Book
    from models.user import User


class Wishlist(BaseModel):
    """Wishlist item model."""
    
    __tablename__ = "wishlists"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user: "User" = relationship("User", back_populates="wishlists")
    
    # Can be linked to existing book or standalone
    book_id = Column(String(36), ForeignKey("books.id"), nullable=True, index=True)
    book: "Book" = relationship("Book")
    
    # Or manual entry
    title = Column(String(500), nullable=True)
    author_name = Column(String(200), nullable=True)
    isbn = Column(String(13), nullable=True)
    
    priority = Column(Integer, default=1, nullable=False)  # 1-5 priority
    max_price = Column(Numeric(10, 2), nullable=True)
    notes = Column(String(1000), nullable=True)
    
    def __repr__(self) -> str:
        return f"<Wishlist(id={self.id}, user_id={self.user_id}, title={self.title or self.book_id})>"
