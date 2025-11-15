"""
Audio Repository - Media File Data Access Layer

This repository handles all database operations for audio files,
including file metadata, session associations, and storage management.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, desc, asc, and_, or_
from datetime import datetime, timedelta
import uuid

from backend.repositories.base_repository import BaseRepository
from backend.database.models import AudioFile, ConversationSession, User


class AudioFileRepository(BaseRepository[AudioFile]):
    """Repository for AudioFile operations."""

    def __init__(self):
        super().__init__(AudioFile)

    async def create_audio_file(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        filename: str,
        file_path: str,
        file_size: int,
        duration_ms: Optional[int] = None,
        format: str = "wav",
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
        is_input: bool = True,
        audio_metadata: Optional[Dict[str, Any]] = None
    ) -> AudioFile:
        """Create a new audio file record."""
        audio_data = {
            "session_id": session_id,
            "filename": filename,
            "file_path": file_path,
            "file_size": file_size,
            "duration_ms": duration_ms,
            "format": format,
            "sample_rate": sample_rate,
            "channels": channels,
            "is_input": is_input,
            "audio_metadata": audio_metadata or {},
            "created_at": datetime.utcnow()
        }
        return await self.create(db, audio_data)

    async def get_audio_files_for_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        is_input: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[AudioFile]:
        """Get all audio files for a session, optionally filtered by type."""
        try:
            query = select(AudioFile).where(AudioFile.session_id == session_id)

            if is_input is not None:
                query = query.where(AudioFile.is_input == is_input)

            query = query.order_by(desc(AudioFile.created_at))

            if limit:
                query = query.limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get audio files for session {session_id}: {e}")
            raise

    async def get_input_files_for_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: int = 50
    ) -> List[AudioFile]:
        """Get input audio files for a session (user recordings)."""
        return await self.get_audio_files_for_session(
            db, session_id, is_input=True, limit=limit
        )

    async def get_output_files_for_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: int = 50
    ) -> List[AudioFile]:
        """Get output audio files for a session (assistant responses)."""
        return await self.get_audio_files_for_session(
            db, session_id, is_input=False, limit=limit
        )

    async def get_audio_files_for_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        is_input: Optional[bool] = None,
        days: int = 30,
        skip: int = 0,
        limit: int = 100
    ) -> List[Tuple[AudioFile, ConversationSession]]:
        """Get audio files for a user across all their sessions."""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            query = select(AudioFile, ConversationSession).join(
                ConversationSession, AudioFile.session_id == ConversationSession.id
            ).where(
                and_(
                    ConversationSession.user_id == user_id,
                    AudioFile.created_at >= since_date
                )
            )

            if is_input is not None:
                query = query.where(AudioFile.is_input == is_input)

            query = query.order_by(desc(AudioFile.created_at))
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            return result.all()
        except Exception as e:
            self.logger.error(f"Failed to get audio files for user {user_id}: {e}")
            raise

    async def get_audio_files_for_organization(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        is_input: Optional[bool] = None,
        days: int = 30,
        skip: int = 0,
        limit: int = 200
    ) -> List[Tuple[AudioFile, ConversationSession]]:
        """Get audio files for an organization across all sessions."""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            query = select(AudioFile, ConversationSession).join(
                ConversationSession, AudioFile.session_id == ConversationSession.id
            ).where(
                and_(
                    ConversationSession.organization_id == organization_id,
                    AudioFile.created_at >= since_date
                )
            )

            if is_input is not None:
                query = query.where(AudioFile.is_input == is_input)

            query = query.order_by(desc(AudioFile.created_at))
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            return result.all()
        except Exception as e:
            self.logger.error(f"Failed to get audio files for organization {organization_id}: {e}")
            raise

    async def update_audio_metadata(
        self,
        db: AsyncSession,
        audio_file_id: uuid.UUID,
        duration_ms: Optional[int] = None,
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update audio file metadata after processing."""
        try:
            update_data = {}

            if duration_ms is not None:
                update_data["duration_ms"] = duration_ms
            if sample_rate is not None:
                update_data["sample_rate"] = sample_rate
            if channels is not None:
                update_data["channels"] = channels

            if additional_metadata:
                # Merge with existing metadata
                update_data["audio_metadata"] = func.jsonb_set(
                    AudioFile.audio_metadata,
                    text("'{}'"),
                    text(f"'{additional_metadata}'::jsonb"),
                    True  # create if not exists
                )

            if not update_data:
                return True  # Nothing to update

            result = await db.execute(
                update(AudioFile)
                .where(AudioFile.id == audio_file_id)
                .values(**update_data)
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to update audio metadata {audio_file_id}: {e}")
            raise

    async def get_session_audio_count(
        self,
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> Dict[str, int]:
        """Get count of input and output audio files for a session."""
        try:
            # Count input files
            input_result = await db.execute(
                select(func.count())
                .where(
                    and_(
                        AudioFile.session_id == session_id,
                        AudioFile.is_input == True
                    )
                )
            )
            input_count = input_result.scalar()

            # Count output files
            output_result = await db.execute(
                select(func.count())
                .where(
                    and_(
                        AudioFile.session_id == session_id,
                        AudioFile.is_input == False
                    )
                )
            )
            output_count = output_result.scalar()

            return {
                "input_files": input_count,
                "output_files": output_count,
                "total_files": input_count + output_count
            }
        except Exception as e:
            self.logger.error(f"Failed to get audio count for session {session_id}: {e}")
            raise

    async def get_audio_analytics(
        self,
        db: AsyncSession,
        organization_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get audio file analytics."""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            # Base query
            base_query = select(AudioFile).join(
                ConversationSession, AudioFile.session_id == ConversationSession.id
            ).where(AudioFile.created_at >= since_date)

            if organization_id:
                base_query = base_query.where(
                    ConversationSession.organization_id == organization_id
                )
            elif user_id:
                base_query = base_query.where(
                    ConversationSession.user_id == user_id
                )

            # Total files
            total_result = await db.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            total_files = total_result.scalar()

            # Input vs output files
            input_result = await db.execute(
                select(func.count())
                .select_from(base_query.subquery())
                .where(AudioFile.is_input == True)
            )
            input_files = input_result.scalar()

            output_files = total_files - input_files

            # Total storage used
            storage_result = await db.execute(
                select(func.sum(AudioFile.file_size))
                .select_from(base_query.subquery())
            )
            total_storage_bytes = storage_result.scalar() or 0

            # Average duration
            duration_result = await db.execute(
                select(func.avg(AudioFile.duration_ms))
                .select_from(base_query.subquery())
                .where(AudioFile.duration_ms.isnot(None))
            )
            avg_duration_ms = duration_result.scalar() or 0

            # Files by format
            format_result = await db.execute(
                select(
                    AudioFile.format,
                    func.count().label('count')
                )
                .select_from(base_query.subquery())
                .group_by(AudioFile.format)
            )
            files_by_format = {row.format: row.count for row in format_result}

            # Files by sample rate
            sample_rate_result = await db.execute(
                select(
                    AudioFile.sample_rate,
                    func.count().label('count')
                )
                .select_from(base_query.subquery())
                .where(AudioFile.sample_rate.isnot(None))
                .group_by(AudioFile.sample_rate)
            )
            files_by_sample_rate = {
                str(row.sample_rate): row.count for row in sample_rate_result
            }

            return {
                "period_days": days,
                "total_files": total_files,
                "input_files": input_files,
                "output_files": output_files,
                "total_storage_bytes": total_storage_bytes,
                "total_storage_mb": round(total_storage_bytes / (1024 * 1024), 2),
                "avg_duration_ms": round(avg_duration_ms, 0),
                "avg_duration_seconds": round(avg_duration_ms / 1000, 1) if avg_duration_ms else 0,
                "files_by_format": files_by_format,
                "files_by_sample_rate": files_by_sample_rate,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to get audio analytics: {e}")
            raise

    async def cleanup_old_audio_files(
        self,
        db: AsyncSession,
        days_old: int = 90,
        batch_size: int = 100
    ) -> int:
        """Clean up old audio file records."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Find audio files to delete
            result = await db.execute(
                select(AudioFile.id)
                .where(AudioFile.created_at < cutoff_date)
                .limit(batch_size)
            )
            file_ids = [row.id for row in result]

            if not file_ids:
                return 0

            # Delete the records
            delete_result = await db.execute(
                delete(AudioFile).where(AudioFile.id.in_(file_ids))
            )

            await db.commit()
            deleted_count = delete_result.rowcount

            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old audio file records")

            return deleted_count

        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to cleanup old audio files: {e}")
            raise

    async def get_large_files(
        self,
        db: AsyncSession,
        min_size_mb: int = 10,
        organization_id: Optional[uuid.UUID] = None,
        limit: int = 50
    ) -> List[Tuple[AudioFile, ConversationSession]]:
        """Get large audio files for cleanup or analysis."""
        try:
            min_size_bytes = min_size_mb * 1024 * 1024

            query = select(AudioFile, ConversationSession).join(
                ConversationSession, AudioFile.session_id == ConversationSession.id
            ).where(AudioFile.file_size >= min_size_bytes)

            if organization_id:
                query = query.where(
                    ConversationSession.organization_id == organization_id
                )

            query = query.order_by(desc(AudioFile.file_size)).limit(limit)

            result = await db.execute(query)
            return result.all()
        except Exception as e:
            self.logger.error(f"Failed to get large files: {e}")
            raise

    async def get_orphaned_files(
        self,
        db: AsyncSession,
        limit: int = 100
    ) -> List[AudioFile]:
        """Get audio files that reference non-existent sessions."""
        try:
            # Find audio files with invalid session references
            result = await db.execute(
                select(AudioFile)
                .where(
                    ~AudioFile.session_id.in_(
                        select(ConversationSession.id)
                    )
                )
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get orphaned files: {e}")
            raise

    async def delete_orphaned_files(
        self,
        db: AsyncSession,
        batch_size: int = 50
    ) -> int:
        """Delete audio files that reference non-existent sessions."""
        try:
            # Get orphaned files
            orphaned_files = await self.get_orphaned_files(db, limit=batch_size)

            if not orphaned_files:
                return 0

            orphaned_ids = [f.id for f in orphaned_files]

            # Delete the orphaned records
            delete_result = await db.execute(
                delete(AudioFile).where(AudioFile.id.in_(orphaned_ids))
            )

            await db.commit()
            deleted_count = delete_result.rowcount

            if deleted_count > 0:
                self.logger.info(f"Deleted {deleted_count} orphaned audio file records")

            return deleted_count

        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to delete orphaned files: {e}")
            raise