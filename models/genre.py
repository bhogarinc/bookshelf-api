"""Genre model for book categorization."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.book import Book


class Genre(BaseModel):
    """Genre/category model."""
    
    __tablename__ = "genres"
    
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    
    # Relationships
    books: List["Book"] = relationship("Book", back_populates="genre", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<Genre(id={self.id}, name={self.name})>"
