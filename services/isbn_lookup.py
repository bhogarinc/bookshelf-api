"""ISBN lookup service using external APIs."""

import logging
from typing import Optional

import httpx

from config.settings import settings
from schemas.book import ISBNLookupResponse

logger = logging.getLogger(__name__)


class ISBNLookupService:
    """Service for looking up book information by ISBN."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.google_books_url = "https://www.googleapis.com/books/v1/volumes"
        self.open_library_url = settings.open_library_api_url
    
    async def lookup(self, isbn: str) -> Optional[ISBNLookupResponse]:
        """Lookup book by ISBN using multiple sources."""
        # Try Google Books first
        result = await self._lookup_google_books(isbn)
        if result:
            return result
        
        # Fallback to Open Library
        result = await self._lookup_open_library(isbn)
        if result:
            return result
        
        logger.warning(f"ISBN not found: {isbn}")
        return None
    
    async def _lookup_google_books(self, isbn: str) -> Optional[ISBNLookupResponse]:
        """Lookup using Google Books API."""
        try:
            params = {"q": f"isbn:{isbn}"}
            if settings.google_books_api_key:
                params["key"] = settings.google_books_api_key
            
            response = await self.client.get(self.google_books_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("items"):
                return None
            
            volume = data["items"][0]["volumeInfo"]
            
            return ISBNLookupResponse(
                isbn=isbn,
                title=volume.get("title", ""),
                subtitle=volume.get("subtitle"),
                authors=volume.get("authors", []),
                publisher=volume.get("publisher"),
                published_date=volume.get("publishedDate"),
                description=volume.get("description"),
                page_count=volume.get("pageCount"),
                categories=volume.get("categories", []),
                cover_image_url=volume.get("imageLinks", {}).get("thumbnail"),
                language=volume.get("language")
            )
        except Exception as e:
            logger.error(f"Google Books lookup error: {e}")
            return None
    
    async def _lookup_open_library(self, isbn: str) -> Optional[ISBNLookupResponse]:
        """Lookup using Open Library API."""
        try:
            url = f"{self.open_library_url}/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            key = f"ISBN:{isbn}"
            if key not in data:
                return None
            
            book_data = data[key]
            
            return ISBNLookupResponse(
                isbn=isbn,
                title=book_data.get("title", ""),
                subtitle=book_data.get("subtitle"),
                authors=[a.get("name") for a in book_data.get("authors", [])],
                publisher=book_data.get("publishers", [{}])[0].get("name") if book_data.get("publishers") else None,
                published_date=str(book_data.get("publish_date")) if book_data.get("publish_date") else None,
                description=book_data.get("notes"),
                page_count=book_data.get("number_of_pages"),
                categories=[s.get("name") for s in book_data.get("subjects", [])],
                cover_image_url=book_data.get("cover", {}).get("medium"),
                language=None
            )
        except Exception as e:
            logger.error(f"Open Library lookup error: {e}")
            return None
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
