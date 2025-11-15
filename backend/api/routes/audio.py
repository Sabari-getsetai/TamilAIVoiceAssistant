"""
Audio API Endpoints for Tamil AI Voice Assistant

Provides endpoints for:
- Audio file access via presigned URLs
- Audio metrics and monitoring
- Audio file information and metadata
- Secure download for stored audio files
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


from fastapi import APIRouter, HTTPException, Depends, Query, Path as PathParam
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_db
from backend.database.models import AudioFile, ConversationSession
from backend.storage.minio_client import get_minio_client
from backend.services.tier_service import UserTierService, get_retention_for_session
from backend.settings import settings
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/audio", tags=["audio"])

# Optional security (if you want to add JWT authentication)
security = HTTPBearer(auto_error=False)


@router.get("/presigned-url/{audio_file_id}")
async def get_audio_presigned_url(
    audio_file_id: str = PathParam(..., description="Audio file ID"),
    session_id: str = Query(..., description="Session ID for authentication"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get presigned URL for audio file download.

    Args:
        audio_file_id: The audio file ID to get URL for
        session_id: Session ID for access validation
        db: Database session

    Returns:
        Dictionary containing presigned URL and file metadata

    Raises:
        HTTPException: If file not found, session invalid, or access denied
    """
    try:
        # Validate session exists and get user tier
        session_stmt = select(ConversationSession).where(ConversationSession.id == session_id)
        session_result = await db.execute(session_stmt)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get audio file with session validation
        audio_stmt = select(AudioFile).where(
            and_(
                AudioFile.id == audio_file_id,
                AudioFile.session_id == session_id
            )
        )
        audio_result = await db.execute(audio_stmt)
        audio_file = audio_result.scalar_one_or_none()

        if not audio_file:
            raise HTTPException(status_code=404, detail="Audio file not found or access denied")

        # Check if file has expired based on retention policy
        user_tier = await UserTierService.get_user_tier_by_session_id(session_id, db)
        retention_hours = await get_retention_for_session(session_id, db)

        if audio_file.created_at:
            expiry_time = audio_file.created_at + timedelta(hours=retention_hours)
            if datetime.utcnow() > expiry_time:
                raise HTTPException(
                    status_code=410,
                    detail=f"Audio file expired. {user_tier} tier retention: {retention_hours}h"
                )

        # Generate presigned URL
        minio_client = get_minio_client()
        bucket_name = settings.MINIO_AUDIO_BUCKET

        # Check if file exists in MinIO
        try:
            minio_client.stat_object(bucket_name, audio_file.file_path)
        except Exception as e:
            logger.error(f"Audio file not found in MinIO: {audio_file.file_path} - {e}")
            raise HTTPException(status_code=404, detail="Audio file not found in storage")

        # Generate presigned URL (valid for configured time)
        presigned_url = minio_client.presigned_get_object(
            bucket_name,
            audio_file.file_path,
            expires=timedelta(minutes=settings.AUDIO_PRESIGNED_URL_EXPIRY_MINUTES)
        )

        # Log access for metrics
        logger.info(f"Generated presigned URL for audio {audio_file_id} (session: {session_id}, user_tier: {user_tier})")

        return {
            "presigned_url": presigned_url,
            "file_id": audio_file.id,
            "filename": audio_file.filename,
            "file_type": audio_file.file_type.value if audio_file.file_type else "unknown",
            "file_size": audio_file.file_size,
            "duration_seconds": audio_file.duration_seconds,
            "created_at": audio_file.created_at.isoformat() if audio_file.created_at else None,
            "expires_at": (
                audio_file.created_at + timedelta(hours=retention_hours)
            ).isoformat() if audio_file.created_at else None,
            "user_tier": user_tier,
            "url_expires_in_minutes": settings.AUDIO_PRESIGNED_URL_EXPIRY_MINUTES
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating presigned URL for audio {audio_file_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/session/{session_id}/files")
async def list_session_audio_files(
    session_id: str = PathParam(..., description="Session ID"),
    include_expired: bool = Query(False, description="Include expired files"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all audio files for a session.

    Args:
        session_id: Session ID to list files for
        include_expired: Whether to include expired files
        db: Database session

    Returns:
        Dictionary containing list of audio files with metadata
    """
    try:
        # Validate session
        session_stmt = select(ConversationSession).where(ConversationSession.id == session_id)
        session_result = await db.execute(session_stmt)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get retention policy
        user_tier = await UserTierService.get_user_tier_by_session_id(session_id, db)
        retention_hours = await get_retention_for_session(session_id, db)

        # Get all audio files for session
        audio_stmt = select(AudioFile).where(AudioFile.session_id == session_id)
        audio_result = await db.execute(audio_stmt)
        audio_files = audio_result.scalars().all()

        # Process files and check expiry
        files_data = []
        current_time = datetime.utcnow()

        for audio_file in audio_files:
            # Check if expired
            is_expired = False
            if audio_file.created_at:
                expiry_time = audio_file.created_at + timedelta(hours=retention_hours)
                is_expired = current_time > expiry_time

            # Skip expired files if not requested
            if is_expired and not include_expired:
                continue

            file_data = {
                "id": audio_file.id,
                "filename": audio_file.filename,
                "file_type": audio_file.file_type.value if audio_file.file_type else "unknown",
                "file_size": audio_file.file_size,
                "duration_seconds": audio_file.duration_seconds,
                "created_at": audio_file.created_at.isoformat() if audio_file.created_at else None,
                "expires_at": (
                    audio_file.created_at + timedelta(hours=retention_hours)
                ).isoformat() if audio_file.created_at else None,
                "is_expired": is_expired,
                "turn_id": audio_file.turn_id
            }
            files_data.append(file_data)

        return {
            "session_id": session_id,
            "user_tier": user_tier,
            "retention_hours": retention_hours,
            "total_files": len(files_data),
            "files": files_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing audio files for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/file/{audio_file_id}/info")
async def get_audio_file_info(
    audio_file_id: str = PathParam(..., description="Audio file ID"),
    session_id: str = Query(..., description="Session ID for authentication"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed information about an audio file.

    Args:
        audio_file_id: Audio file ID
        session_id: Session ID for access validation
        db: Database session

    Returns:
        Detailed audio file information
    """
    try:
        # Validate session and get file
        audio_stmt = select(AudioFile).where(
            and_(
                AudioFile.id == audio_file_id,
                AudioFile.session_id == session_id
            )
        )
        audio_result = await db.execute(audio_stmt)
        audio_file = audio_result.scalar_one_or_none()

        if not audio_file:
            raise HTTPException(status_code=404, detail="Audio file not found or access denied")

        # Get tier information
        user_tier = await UserTierService.get_user_tier_by_session_id(session_id, db)
        retention_hours = await get_retention_for_session(session_id, db)

        # Check expiry status
        is_expired = False
        expires_at = None
        if audio_file.created_at:
            expires_at = audio_file.created_at + timedelta(hours=retention_hours)
            is_expired = datetime.utcnow() > expires_at

        # Check MinIO availability
        minio_available = False
        minio_client = get_minio_client()
        try:
            minio_client.stat_object(settings.MINIO_AUDIO_BUCKET, audio_file.file_path)
            minio_available = True
        except Exception:
            pass

        return {
            "id": audio_file.id,
            "filename": audio_file.filename,
            "file_path": audio_file.file_path,
            "file_type": audio_file.file_type.value if audio_file.file_type else "unknown",
            "file_size": audio_file.file_size,
            "duration_seconds": audio_file.duration_seconds,
            "created_at": audio_file.created_at.isoformat() if audio_file.created_at else None,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "is_expired": is_expired,
            "available_in_storage": minio_available,
            "session_id": session_id,
            "turn_id": audio_file.turn_id,
            "user_tier": user_tier,
            "retention_hours": retention_hours,
            "metadata": audio_file.metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audio file info for {audio_file_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metrics/session/{session_id}")
async def get_session_audio_metrics(
    session_id: str = PathParam(..., description="Session ID"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get audio metrics for a session.

    Args:
        session_id: Session ID
        db: Database session

    Returns:
        Audio metrics and usage statistics
    """
    try:
        # Validate session
        session_stmt = select(ConversationSession).where(ConversationSession.id == session_id)
        session_result = await db.execute(session_stmt)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get all audio files for session
        audio_stmt = select(AudioFile).where(AudioFile.session_id == session_id)
        audio_result = await db.execute(audio_stmt)
        audio_files = audio_result.scalars().all()

        # Calculate metrics
        total_files = len(audio_files)
        total_size = sum(f.file_size or 0 for f in audio_files)
        total_duration = sum(f.duration_seconds or 0 for f in audio_files)

        # Group by file type
        type_stats = {}
        for audio_file in audio_files:
            file_type = audio_file.file_type.value if audio_file.file_type else "unknown"
            if file_type not in type_stats:
                type_stats[file_type] = {"count": 0, "size": 0, "duration": 0}

            type_stats[file_type]["count"] += 1
            type_stats[file_type]["size"] += audio_file.file_size or 0
            type_stats[file_type]["duration"] += audio_file.duration_seconds or 0

        # Get tier information
        user_tier = await UserTierService.get_user_tier_by_session_id(session_id, db)
        retention_hours = await get_retention_for_session(session_id, db)

        # Check storage usage against tier limits
        tier_features = UserTierService._get_tier_features(user_tier)
        max_audio_duration = tier_features.get("max_audio_duration_minutes", -1)

        return {
            "session_id": session_id,
            "user_tier": user_tier,
            "retention_hours": retention_hours,
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_duration_seconds": total_duration,
            "total_duration_minutes": round(total_duration / 60, 2),
            "files_by_type": type_stats,
            "tier_limits": {
                "max_audio_duration_minutes": max_audio_duration,
                "retention_hours": retention_hours
            },
            "usage_warnings": {
                "approaching_duration_limit": (
                    max_audio_duration > 0 and
                    total_duration / 60 > max_audio_duration * 0.8
                ),
                "exceeding_duration_limit": (
                    max_audio_duration > 0 and
                    total_duration / 60 > max_audio_duration
                )
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audio metrics for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")