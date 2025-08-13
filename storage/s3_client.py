"""S3 storage client with lazy boto3 import and environment-based configuration."""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _get_s3_client():
    """Get configured S3 client with lazy boto3 import.

    Returns:
        boto3 S3 client

    Raises:
        RuntimeError: If boto3 is not available or configuration is incomplete
    """
    try:
        import boto3
    except ImportError:
        raise RuntimeError(
            "boto3 is not installed. Please install it with: pip install boto3"
        )

    # Check required environment variables
    required_vars = ["S3_BUCKET", "S3_REGION", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise RuntimeError(
            f"Missing required S3 environment variables: {', '.join(missing_vars)}. "
            f"Please set: {', '.join(required_vars)}"
        )

    # Create S3 client with explicit credentials
    s3_client = boto3.client(
        's3',
        region_name=os.getenv("S3_REGION"),
        aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY")
    )

    return s3_client


def upload_file(bucket: str, key: str, file_path: str) -> str:
    """Upload a file to S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key (path)
        file_path: Local file path to upload

    Returns:
        S3 object URL

    Raises:
        RuntimeError: If boto3 not available or env vars missing
        FileNotFoundError: If local file doesn't exist
        Exception: For S3 upload errors
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    s3_client = _get_s3_client()

    try:
        # Upload file
        s3_client.upload_file(file_path, bucket, key)

        # Return object URL
        region = os.getenv("S3_REGION")
        object_url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"

        logger.info(f"Successfully uploaded {file_path} to s3://{bucket}/{key}")
        return object_url

    except Exception as e:
        logger.error(f"Failed to upload file to S3: {e}")
        raise


def presigned_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for S3 object access.

    Args:
        bucket: S3 bucket name
        key: S3 object key
        expires_in: URL expiration time in seconds (default: 1 hour)

    Returns:
        Presigned URL string

    Raises:
        RuntimeError: If boto3 not available or env vars missing
        Exception: For S3 API errors
    """
    s3_client = _get_s3_client()

    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expires_in
        )

        logger.debug(f"Generated presigned URL for s3://{bucket}/{key} (expires in {expires_in}s)")
        return url

    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise


def delete_file(bucket: str, key: str) -> None:
    """Delete a file from S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key to delete

    Raises:
        RuntimeError: If boto3 not available or env vars missing
        Exception: For S3 delete errors
    """
    s3_client = _get_s3_client()

    try:
        s3_client.delete_object(Bucket=bucket, Key=key)
        logger.info(f"Successfully deleted s3://{bucket}/{key}")

    except Exception as e:
        logger.error(f"Failed to delete S3 object: {e}")
        raise


def list_objects(bucket: str, prefix: str = "", max_keys: int = 1000) -> list:
    """List objects in S3 bucket with optional prefix filter.

    Args:
        bucket: S3 bucket name
        prefix: Object key prefix to filter by
        max_keys: Maximum number of objects to return

    Returns:
        List of object metadata dictionaries

    Raises:
        RuntimeError: If boto3 not available or env vars missing
        Exception: For S3 API errors
    """
    s3_client = _get_s3_client()

    try:
        params = {
            'Bucket': bucket,
            'MaxKeys': max_keys
        }

        if prefix:
            params['Prefix'] = prefix

        response = s3_client.list_objects_v2(**params)

        objects = []
        if 'Contents' in response:
            for obj in response['Contents']:
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'].strip('"')
                })

        logger.debug(f"Listed {len(objects)} objects from s3://{bucket}/{prefix}")
        return objects

    except Exception as e:
        logger.error(f"Failed to list S3 objects: {e}")
        raise


def object_exists(bucket: str, key: str) -> bool:
    """Check if an object exists in S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        True if object exists, False otherwise

    Raises:
        RuntimeError: If boto3 not available or env vars missing
    """
    s3_client = _get_s3_client()

    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except s3_client.exceptions.NoSuchKey:
        return False
    except Exception as e:
        logger.error(f"Error checking S3 object existence: {e}")
        raise


def get_object_metadata(bucket: str, key: str) -> Optional[dict]:
    """Get metadata for an S3 object.

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        Object metadata dictionary or None if object doesn't exist

    Raises:
        RuntimeError: If boto3 not available or env vars missing
        Exception: For S3 API errors (except NoSuchKey)
    """
    s3_client = _get_s3_client()

    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)

        return {
            'content_length': response.get('ContentLength'),
            'content_type': response.get('ContentType'),
            'last_modified': response.get('LastModified'),
            'etag': response.get('ETag', '').strip('"'),
            'metadata': response.get('Metadata', {})
        }

    except s3_client.exceptions.NoSuchKey:
        return None
    except Exception as e:
        logger.error(f"Failed to get S3 object metadata: {e}")
        raise
