"""
Storage package for Tamil AI Voice Assistant.

This package handles:
- MinIO object storage configuration
- File upload and download utilities
- Bucket management
- Pre-signed URL generation
"""

from .minio_client import get_minio_client, init_buckets, upload_file, download_file, get_presigned_url
from .file_manager import FileManager

__all__ = [
    "get_minio_client",
    "init_buckets",
    "upload_file",
    "download_file",
    "get_presigned_url",
    "FileManager"
]