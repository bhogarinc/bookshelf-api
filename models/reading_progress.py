"""Reading progress tracking model."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.book import Book
    from models.user import User


class ReadingProgress(BaseModel):
    """Reading progress tracking model."""
    
    __tablename__ = "reading_progress"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user: "User" = relationship("User", back_populates="reading_progress")
    
    book_id = Column(String(36), ForeignKey("books.id"), nullable=False, index=True)
    book: "Book" = relationship("Book", back_populates="reading_progress")
    
    # Progress
    current_page = Column(Integer, nullable=False, default=0)
    total_pages = Column(Integer, nullable=False)
    percentage_complete = Column(Numeric(5, 2), nullable=False, default=0)
    
    # Sessions
    reading_sessions = Column(Integer, default=1, nullable=False)
    total_reading_time_minutes = Column(Integer, default=0, nullable=False)
    
    # Dates
    started_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    estimated_completion_date = Column(Date, nullable=True)
    
    def calculate_percentage(self) -> None:
        """Calculate completion percentage."""
        if self.total_pages and self.total_pages > 0:
            self.percentage_complete = (self.current_page / self.total_pages) * 100
    
    def __repr__(self) -> str:
        return f"<ReadingProgress(user_id={self.user_id}, book_id={self.book_id}, {self.percentage_complete}%)>"
