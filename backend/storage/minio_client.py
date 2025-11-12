"""
MinIO client configuration and utilities for Tamil AI Voice Assistant.

This module provides:
- MinIO client initialization
- Bucket creation and management
- File upload/download operations
- Pre-signed URL generation for secure access
- Error handling for storage operations
- Retry mechanisms with exponential backoff
- Docker service integration
"""

import os
import time
import logging
from datetime import timedelta
from typing import Optional, Dict, Any, BinaryIO
from io import BytesIO

from minio import Minio
from minio.error import S3Error
from urllib3.exceptions import MaxRetryError

logger = logging.getLogger(__name__)

# Detect if running in Docker
IS_DOCKER = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER', 'false').lower() == 'true'

# MinIO configuration with environment variable support
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")

if not MINIO_ENDPOINT:
    # Fallback construction for endpoint if not set
    minio_host = "minio" if IS_DOCKER else "localhost"
    minio_port = os.getenv("MINIO_PORT", "9000")
    MINIO_ENDPOINT = f"{minio_host}:{minio_port}"
    logger.info(f"Constructed MINIO_ENDPOINT for {'Docker' if IS_DOCKER else 'local'} environment: {MINIO_ENDPOINT}")
else:
    logger.info(f"Using MINIO_ENDPOINT from environment variable: {MINIO_ENDPOINT}")

# MinIO credentials - prioritize MINIO_ACCESS_KEY/SECRET_KEY, fallback to ROOT credentials
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY") or os.getenv("MINIO_ROOT_USER", "tamil_admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY") or os.getenv("MINIO_ROOT_PASSWORD", "tamil_minio_password_dev")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Bucket names
DOCUMENTS_BUCKET = os.getenv("MINIO_DOCUMENTS_BUCKET", "tamil-assistant-documents")
AUDIO_BUCKET = os.getenv("MINIO_AUDIO_BUCKET", "tamil-assistant-audio")

# Global MinIO client instance
_minio_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    """
    Get or create MinIO client instance.

    Returns:
        Minio: Configured MinIO client

    Raises:
        ConnectionError: If unable to connect to MinIO server
    """
    global _minio_client

    if _minio_client is None:
        try:
            _minio_client = Minio(
                endpoint=MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE,
            )

            # Test connection
            _minio_client.list_buckets()
            logger.info(f"MinIO client connected to {MINIO_ENDPOINT}")

        except (S3Error, MaxRetryError) as e:
            logger.error(f"Failed to connect to MinIO: {e}")
            raise ConnectionError(f"Cannot connect to MinIO server at {MINIO_ENDPOINT}")

    return _minio_client


async def wait_for_minio(timeout: float = 60.0) -> bool:
    """
    Wait for MinIO to become available.
    
    Args:
        timeout: Maximum time to wait in seconds
        
    Returns:
        bool: True if MinIO is available, False if timeout
    """
    from infrastructure.retry import wait_for_service
    
    logger.info("Waiting for MinIO to become available...")
    return await wait_for_service(
        health_check=check_minio_health,
        service_name="MinIO",
        timeout=timeout,
        check_interval=2.0
    )


async def init_buckets():
    """
    Initialize required MinIO buckets with proper policies.

    This function:
    1. Creates required buckets if they don't exist
    2. Sets up lifecycle policies for automatic cleanup
    3. Configures access policies for security
    """
    client = get_minio_client()

    buckets_to_create = [
        {
            "name": DOCUMENTS_BUCKET,
            "description": "User-uploaded documents (PDF, DOCX, etc.)",
            "lifecycle_days": 0,  # No automatic deletion
        },
        {
            "name": AUDIO_BUCKET,
            "description": "Audio files (user input, TTS output, refined)",
            "lifecycle_days": 1,  # Delete after 24 hours
        }
    ]

    for bucket_config in buckets_to_create:
        bucket_name = bucket_config["name"]

        try:
            # Check if bucket exists
            if not client.bucket_exists(bucket_name):
                # Create bucket
                client.make_bucket(bucket_name)
                logger.info(f"Created MinIO bucket: {bucket_name}")

                # Set lifecycle policy for automatic cleanup
                if bucket_config["lifecycle_days"] > 0:
                    lifecycle_config = {
                        "Rules": [
                            {
                                "ID": "auto-delete",
                                "Status": "Enabled",
                                "Filter": {"Prefix": ""},
                                "Expiration": {"Days": bucket_config["lifecycle_days"]}
                            }
                        ]
                    }
                    try:
                        client.set_bucket_lifecycle(bucket_name, lifecycle_config)
                        logger.info(f"Set lifecycle policy for {bucket_name}: {bucket_config['lifecycle_days']} days")
                    except S3Error as e:
                        logger.warning(f"Could not set lifecycle policy for {bucket_name}: {e}")

            else:
                logger.info(f"MinIO bucket already exists: {bucket_name}")

        except S3Error as e:
            # Handle bucket already exists errors
            if "BucketAlreadyExists" in str(e) or "BucketAlreadyOwnedByYou" in str(e):
                logger.info(f"MinIO bucket already exists: {bucket_name}")
            else:
                logger.error(f"Error creating bucket {bucket_name}: {e}")
                raise


async def init_buckets_with_retry(max_retries: int = 5, initial_delay: float = 1.0):
    """
    Initialize MinIO buckets with retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
    """
    from infrastructure.retry import retry_with_backoff, RetryConfig
    
    config = RetryConfig(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True
    )
    
    logger.info("Initializing MinIO buckets with retry logic...")
    
    try:
        # First wait for MinIO to be available
        minio_available = await wait_for_minio(timeout=60.0)
        
        if not minio_available:
            logger.error("MinIO did not become available within timeout")
            raise ConnectionError("MinIO connection timeout")
        
        # Then initialize with retry
        await retry_with_backoff(
            operation=init_buckets,
            config=config,
            operation_name="minio_bucket_initialization"
        )
        
        logger.info("MinIO buckets initialized successfully with retry logic")
        
    except Exception as e:
        logger.error(f"Failed to initialize MinIO buckets after retries: {e}")
        raise


def upload_file(
    bucket_name: str,
    object_name: str,
    file_data: BinaryIO,
    content_type: str = "application/octet-stream",
    metadata: Optional[Dict[str, str]] = None
) -> bool:
    """
    Upload a file to MinIO bucket.

    Args:
        bucket_name: Target bucket name
        object_name: Object key/path in bucket
        file_data: File data to upload
        content_type: MIME type of the file
        metadata: Optional metadata to attach to the object

    Returns:
        bool: True if upload successful, False otherwise
    """
    try:
        client = get_minio_client()

        # Prepare metadata
        if metadata is None:
            metadata = {}

        # Add upload timestamp
        metadata["upload_timestamp"] = str(int(time.time()))

        # Get file size
        file_data.seek(0, 2)  # Seek to end
        file_size = file_data.tell()
        file_data.seek(0)  # Seek back to beginning

        # Upload file
        client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=file_data,
            length=file_size,
            content_type=content_type,
            metadata=metadata
        )

        logger.info(f"Successfully uploaded {object_name} to {bucket_name}")
        return True

    except S3Error as e:
        logger.error(f"Error uploading file {object_name} to {bucket_name}: {e}")
        return False


def download_file(bucket_name: str, object_name: str) -> Optional[BytesIO]:
    """
    Download a file from MinIO bucket.

    Args:
        bucket_name: Source bucket name
        object_name: Object key/path in bucket

    Returns:
        BytesIO: File data if successful, None otherwise
    """
    try:
        client = get_minio_client()

        response = client.get_object(bucket_name, object_name)
        file_data = BytesIO(response.read())
        response.close()
        response.release_conn()

        logger.info(f"Successfully downloaded {object_name} from {bucket_name}")
        return file_data

    except S3Error as e:
        logger.error(f"Error downloading file {object_name} from {bucket_name}: {e}")
        return None


def get_presigned_url(
    bucket_name: str,
    object_name: str,
    expires: timedelta = timedelta(minutes=15),
    method: str = "GET"
) -> Optional[str]:
    """
    Generate a pre-signed URL for temporary access to an object.

    Args:
        bucket_name: Bucket containing the object
        object_name: Object key/path
        expires: URL expiration time (default: 15 minutes)
        method: HTTP method (GET, PUT, DELETE)

    Returns:
        str: Pre-signed URL if successful, None otherwise
    """
    try:
        client = get_minio_client()

        if method.upper() == "GET":
            url = client.presigned_get_object(bucket_name, object_name, expires=expires)
        elif method.upper() == "PUT":
            url = client.presigned_put_object(bucket_name, object_name, expires=expires)
        elif method.upper() == "DELETE":
            url = client.presigned_delete_object(bucket_name, object_name, expires=expires)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None

        logger.debug(f"Generated pre-signed {method} URL for {object_name} (expires in {expires})")
        return url

    except S3Error as e:
        logger.error(f"Error generating pre-signed URL for {object_name}: {e}")
        return None


def delete_file(bucket_name: str, object_name: str) -> bool:
    """
    Delete a file from MinIO bucket.

    Args:
        bucket_name: Bucket containing the object
        object_name: Object key/path to delete

    Returns:
        bool: True if deletion successful, False otherwise
    """
    try:
        client = get_minio_client()
        client.remove_object(bucket_name, object_name)

        logger.info(f"Successfully deleted {object_name} from {bucket_name}")
        return True

    except S3Error as e:
        logger.error(f"Error deleting file {object_name} from {bucket_name}: {e}")
        return False


def list_objects(
    bucket_name: str,
    prefix: str = "",
    recursive: bool = True
) -> list:
    """
    List objects in a MinIO bucket.

    Args:
        bucket_name: Bucket to list objects from
        prefix: Object key prefix to filter by
        recursive: Whether to list recursively

    Returns:
        list: List of object information
    """
    try:
        client = get_minio_client()
        objects = client.list_objects(bucket_name, prefix=prefix, recursive=recursive)

        object_list = []
        for obj in objects:
            object_list.append({
                "name": obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified,
                "etag": obj.etag,
                "content_type": obj.content_type
            })

        logger.debug(f"Listed {len(object_list)} objects from {bucket_name} with prefix '{prefix}'")
        return object_list

    except S3Error as e:
        logger.error(f"Error listing objects from {bucket_name}: {e}")
        return []


async def check_minio_health() -> bool:
    """
    Check if MinIO server is healthy and accessible.

    Returns:
        bool: True if MinIO is healthy, False otherwise
    """
    try:
        client = get_minio_client()
        # Try to list buckets as a health check
        buckets = client.list_buckets()
        logger.debug(f"MinIO health check passed. Found {len(buckets)} buckets.")
        return True

    except Exception as e:
        logger.debug(f"MinIO health check failed: {e}")
        return False


async def get_minio_info() -> dict:
    """
    Get MinIO connection information.
    
    Returns:
        dict: MinIO connection details
    """
    try:
        client = get_minio_client()
        buckets = client.list_buckets()
        
        bucket_info = []
        for bucket in buckets:
            try:
                # Get bucket stats
                objects = list(client.list_objects(bucket.name, recursive=True))
                total_size = sum(obj.size for obj in objects if obj.size)
                
                bucket_info.append({
                    "name": bucket.name,
                    "creation_date": bucket.creation_date.isoformat() if bucket.creation_date else None,
                    "object_count": len(objects),
                    "total_size_bytes": total_size,
                })
            except Exception as e:
                bucket_info.append({
                    "name": bucket.name,
                    "error": str(e),
                })
        
        return {
            "connected": True,
            "endpoint": MINIO_ENDPOINT,
            "secure": MINIO_SECURE,
            "is_docker": IS_DOCKER,
            "buckets": bucket_info,
        }
        
    except Exception as e:
        logger.error(f"Error getting MinIO info: {e}")
        return {
            "connected": False,
            "error": str(e),
            "endpoint": MINIO_ENDPOINT,
            "is_docker": IS_DOCKER,
        }
