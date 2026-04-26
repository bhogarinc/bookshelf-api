"""Author model for book authors."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.book import Book


class Author(BaseModel):
    """Author model."""
    
    __tablename__ = "authors"
    
    name = Column(String(200), nullable=False, index=True)
    biography = Column(Text, nullable=True)
    birth_year = Column(Integer, nullable=True)
    death_year = Column(Integer, nullable=True)
    nationality = Column(String(100), nullable=True)
    website = Column(String(500), nullable=True)
    photo_url = Column(String(500), nullable=True)
    
    # Relationships
    books: List["Book"] = relationship("Book", back_populates="author", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<Author(id={self.id}, name={self.name})>"
