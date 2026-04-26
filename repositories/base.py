"""Base repository with common CRUD operations."""

import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import asc, desc, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import BaseModel

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository implementing common database operations."""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
        self.logger = logging.getLogger(f"{__name__}.{model.__name__}Repository")
    
    async def get_by_id(self, id: Union[str, int]) -> Optional[ModelType]:
        """Get entity by ID."""
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching {self.model.__name__} by id {id}: {e}")
            raise
    
    async def get_by_ids(self, ids: List[Union[str, int]]) -> List[ModelType]:
        """Get multiple entities by IDs."""
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id.in_(ids))
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching {self.model.__name__} by ids: {e}")
            raise
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """Get all entities with pagination."""
        try:
            query = select(self.model)
            
            if order_by and hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                query = query.order_by(desc(order_column) if order_desc else asc(order_column))
            
            query = query.offset(skip).limit(limit)
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching all {self.model.__name__}: {e}")
            raise
    
    async def count(self, **filters: Any) -> int:
        """Count entities with optional filters."""
        try:
            query = select(func.count(self.model.id))
            
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
            
            result = await self.session.execute(query)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            self.logger.error(f"Error counting {self.model.__name__}: {e}")
            raise
    
    async def create(self, **data: Any) -> ModelType:
        """Create new entity."""
        try:
            entity = self.model(**data)
            self.session.add(entity)
            await self.session.flush()
            self.logger.info(f"Created {self.model.__name__} with id {entity.id}")
            return entity
        except IntegrityError as e:
            self.logger.error(f"Integrity error creating {self.model.__name__}: {e}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    async def create_many(self, data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple entities."""
        try:
            entities = [self.model(**data) for data in data_list]
            self.session.add_all(entities)
            await self.session.flush()
            self.logger.info(f"Created {len(entities)} {self.model.__name__} entities")
            return entities
        except SQLAlchemyError as e:
            self.logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            raise
    
    async def update(self, id: Union[str, int], **data: Any) -> Optional[ModelType]:
        """Update entity by ID."""
        try:
            entity = await self.get_by_id(id)
            if not entity:
                return None
            
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            await self.session.flush()
            self.logger.info(f"Updated {self.model.__name__} with id {id}")
            return entity
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating {self.model.__name__} {id}: {e}")
            raise
    
    async def delete(self, id: Union[str, int]) -> bool:
        """Delete entity by ID."""
        try:
            entity = await self.get_by_id(id)
            if not entity:
                return False
            
            await self.session.delete(entity)
            await self.session.flush()
            self.logger.info(f"Deleted {self.model.__name__} with id {id}")
            return True
        except SQLAlchemyError as e:
            self.logger.error(f"Error deleting {self.model.__name__} {id}: {e}")
            raise
    
    async def exists(self, id: Union[str, int]) -> bool:
        """Check if entity exists."""
        result = await self.session.execute(
            select(func.count(self.model.id)).where(self.model.id == id)
        )
        return (result.scalar() or 0) > 0
