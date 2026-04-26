"""Book review model."""

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.book import Book
    from models.user import User


class Review(BaseModel):
    """Book review model."""
    
    __tablename__ = "reviews"
    
    book_id = Column(String(36), ForeignKey("books.id"), nullable=False, index=True)
    book: "Book" = relationship("Book", back_populates="reviews")
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user: "User" = relationship("User", back_populates="reviews")
    
    rating = Column(Integer, nullable=False)  # 1-5 scale
    content = Column(Text, nullable=True)
    
    # Ensure one review per user per book
    __table_args__ = (
        UniqueConstraint('book_id', 'user_id', name='unique_user_book_review'),
    )
    
    def __repr__(self) -> str:
        return f"<Review(id={self.id}, book_id={self.book_id}, rating={self.rating})>"
