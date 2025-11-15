"""
Base Repository - Generic CRUD Operations

This module provides a base repository class that implements common
database operations using async SQLAlchemy. All specific repositories
inherit from this base class.
"""

from abc import ABC
from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

# Type variable for the SQLAlchemy model
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

logger = logging.getLogger(__name__)


class BaseRepository(Generic[ModelType], ABC):
    """
    Base repository class providing common CRUD operations.

    This class uses generics to provide type-safe database operations
    for any SQLAlchemy model.
    """

    def __init__(self, model_class: type[ModelType]):
        """
        Initialize the repository with a specific model class.

        Args:
            model_class: The SQLAlchemy model class this repository handles
        """
        self.model_class = model_class

    async def create(
        self,
        db: AsyncSession,
        obj_in: CreateSchemaType | Dict[str, Any]
    ) -> ModelType:
        """
        Create a new record in the database.

        Args:
            db: Database session
            obj_in: Data to create the record from (Pydantic model or dict)

        Returns:
            The created database record

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Convert Pydantic model to dict if necessary
            obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in

            # Create new instance
            db_obj = self.model_class(**obj_data)

            # Add to session and commit
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            logger.debug(f"Created new {self.model_class.__name__} with ID: {getattr(db_obj, 'id', 'N/A')}")
            return db_obj

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to create {self.model_class.__name__}: {e}")
            raise

    async def get_by_id(self, db: AsyncSession, record_id: Any) -> Optional[ModelType]:
        """
        Retrieve a record by its ID.

        Args:
            db: Database session
            record_id: The ID of the record to retrieve

        Returns:
            The database record or None if not found
        """
        try:
            result = await db.execute(
                select(self.model_class).where(self.model_class.id == record_id)
            )
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            logger.error(f"Failed to get {self.model_class.__name__} by ID {record_id}: {e}")
            raise

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        Retrieve multiple records with pagination and filtering.

        Args:
            db: Database session
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            filters: Dictionary of filter conditions
            order_by: Column name to order by

        Returns:
            List of database records
        """
        try:
            query = select(self.model_class)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model_class, key):
                        query = query.where(getattr(self.model_class, key) == value)

            # Apply ordering
            if order_by and hasattr(self.model_class, order_by):
                query = query.order_by(getattr(self.model_class, order_by))

            # Apply pagination
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            logger.error(f"Failed to get multiple {self.model_class.__name__} records: {e}")
            raise

    async def update(
        self,
        db: AsyncSession,
        record_id: Any,
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Update an existing record.

        Args:
            db: Database session
            record_id: ID of the record to update
            obj_in: Data to update the record with

        Returns:
            The updated database record or None if not found
        """
        try:
            # Get existing record
            db_obj = await self.get_by_id(db, record_id)
            if not db_obj:
                return None

            # Convert Pydantic model to dict if necessary
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else obj_in

            # Update fields
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            # Update timestamp if available
            if hasattr(db_obj, 'updated_at'):
                setattr(db_obj, 'updated_at', datetime.utcnow())

            await db.commit()
            await db.refresh(db_obj)

            logger.debug(f"Updated {self.model_class.__name__} with ID: {record_id}")
            return db_obj

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to update {self.model_class.__name__} with ID {record_id}: {e}")
            raise

    async def delete(self, db: AsyncSession, record_id: Any) -> bool:
        """
        Delete a record by its ID.

        Args:
            db: Database session
            record_id: ID of the record to delete

        Returns:
            True if the record was deleted, False if not found
        """
        try:
            # Check if record exists
            db_obj = await self.get_by_id(db, record_id)
            if not db_obj:
                return False

            # Delete the record
            await db.delete(db_obj)
            await db.commit()

            logger.debug(f"Deleted {self.model_class.__name__} with ID: {record_id}")
            return True

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to delete {self.model_class.__name__} with ID {record_id}: {e}")
            raise

    async def count(self, db: AsyncSession, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records matching the given filters.

        Args:
            db: Database session
            filters: Dictionary of filter conditions

        Returns:
            Number of matching records
        """
        try:
            query = select(func.count()).select_from(self.model_class)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model_class, key):
                        query = query.where(getattr(self.model_class, key) == value)

            result = await db.execute(query)
            return result.scalar()

        except SQLAlchemyError as e:
            logger.error(f"Failed to count {self.model_class.__name__} records: {e}")
            raise

    async def exists(self, db: AsyncSession, record_id: Any) -> bool:
        """
        Check if a record exists by its ID.

        Args:
            db: Database session
            record_id: ID of the record to check

        Returns:
            True if the record exists, False otherwise
        """
        try:
            result = await db.execute(
                select(func.count()).select_from(self.model_class).where(self.model_class.id == record_id)
            )
            count = result.scalar()
            return count > 0

        except SQLAlchemyError as e:
            logger.error(f"Failed to check existence of {self.model_class.__name__} with ID {record_id}: {e}")
            raise

    async def bulk_create(self, db: AsyncSession, objects: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in a single transaction.

        Args:
            db: Database session
            objects: List of dictionaries containing record data

        Returns:
            List of created database records
        """
        try:
            db_objects = [self.model_class(**obj_data) for obj_data in objects]

            db.add_all(db_objects)
            await db.commit()

            # Refresh all objects
            for db_obj in db_objects:
                await db.refresh(db_obj)

            logger.debug(f"Created {len(db_objects)} {self.model_class.__name__} records")
            return db_objects

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to bulk create {self.model_class.__name__} records: {e}")
            raise

    async def bulk_update(
        self,
        db: AsyncSession,
        filters: Dict[str, Any],
        values: Dict[str, Any]
    ) -> int:
        """
        Update multiple records matching the given filters.

        Args:
            db: Database session
            filters: Dictionary of filter conditions
            values: Dictionary of values to update

        Returns:
            Number of updated records
        """
        try:
            query = update(self.model_class)

            # Apply filters
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)

            # Add updated_at timestamp if available
            if hasattr(self.model_class, 'updated_at'):
                values['updated_at'] = datetime.utcnow()

            query = query.values(**values)

            result = await db.execute(query)
            await db.commit()

            rows_affected = result.rowcount
            logger.debug(f"Updated {rows_affected} {self.model_class.__name__} records")
            return rows_affected

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to bulk update {self.model_class.__name__} records: {e}")
            raise