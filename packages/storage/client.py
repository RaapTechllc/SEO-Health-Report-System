"""Storage backend implementations for local and S3 storage."""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    boto3 = None
    ClientError = Exception
    BOTO3_AVAILABLE = False


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload data to storage.

        Args:
            key: The storage key (path) for the file.
            data: The file contents as bytes.
            content_type: MIME type of the content.

        Returns:
            URL to the uploaded file.
        """
        pass

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Download data from storage.

        Args:
            key: The storage key (path) for the file.

        Returns:
            The file contents as bytes.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a file from storage.

        Args:
            key: The storage key (path) for the file.

        Returns:
            True if deleted, False if file didn't exist.
        """
        pass

    @abstractmethod
    def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a signed URL for secure access to a file.

        Args:
            key: The storage key (path) for the file.
            expires_in: URL expiration time in seconds (default: 1 hour).

        Returns:
            A signed URL string.

        Raises:
            NotImplementedError: If signed URLs are not supported.
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a file exists in storage.

        Args:
            key: The storage key (path) for the file.

        Returns:
            True if the file exists, False otherwise.
        """
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend for development."""

    def __init__(self, base_path: str = "./storage"):
        """Initialize local storage backend.

        Args:
            base_path: Base directory for file storage.
        """
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, key: str) -> Path:
        """Get the full filesystem path for a key."""
        full_path = (self.base_path / key).resolve()
        if not str(full_path).startswith(str(self.base_path)):
            raise ValueError("Invalid key: path traversal detected")
        return full_path

    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload data to local filesystem."""
        file_path = self._get_full_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        return f"file://{file_path}"

    def download(self, key: str) -> bytes:
        """Download data from local filesystem."""
        file_path = self._get_full_path(key)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        return file_path.read_bytes()

    def delete(self, key: str) -> bool:
        """Delete a file from local filesystem."""
        file_path = self._get_full_path(key)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a file:// URL for local files.

        Note: Local storage does not support signed URLs with expiration.
        Returns a file:// URL for development purposes.
        """
        file_path = self._get_full_path(key)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        return f"file://{file_path}"

    def exists(self, key: str) -> bool:
        """Check if a file exists in local filesystem."""
        file_path = self._get_full_path(key)
        return file_path.exists()


class S3StorageBackend(StorageBackend):
    """AWS S3 storage backend for production."""

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
    ):
        """Initialize S3 storage backend.

        Args:
            bucket_name: S3 bucket name. Defaults to S3_BUCKET_NAME env var.
            region: AWS region. Defaults to AWS_REGION env var.
            access_key_id: AWS access key ID. Defaults to AWS_ACCESS_KEY_ID env var.
            secret_access_key: AWS secret access key. Defaults to AWS_SECRET_ACCESS_KEY env var.

        Raises:
            ImportError: If boto3 is not installed.
            ValueError: If bucket_name is not provided.
        """
        if not BOTO3_AVAILABLE:
            raise ImportError(
                "boto3 is required for S3 storage. "
                "Install it with: pip install boto3"
            )

        self.bucket_name = bucket_name or os.environ.get("S3_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME must be provided or set in environment")

        self.region = region or os.environ.get("AWS_REGION", "us-east-1")

        session_kwargs = {}
        ak = access_key_id or os.environ.get("AWS_ACCESS_KEY_ID")
        sk = secret_access_key or os.environ.get("AWS_SECRET_ACCESS_KEY")

        if ak and sk:
            session_kwargs["aws_access_key_id"] = ak
            session_kwargs["aws_secret_access_key"] = sk

        self._client = boto3.client(
            "s3",
            region_name=self.region,
            **session_kwargs
        )

    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload data to S3."""
        self._client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return f"s3://{self.bucket_name}/{key}"

    def download(self, key: str) -> bytes:
        """Download data from S3."""
        try:
            response = self._client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {key}")
            raise

    def delete(self, key: str) -> bool:
        """Delete a file from S3."""
        if not self.exists(key):
            return False
        self._client.delete_object(Bucket=self.bucket_name, Key=key)
        return True

    def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for secure S3 access."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )

    def exists(self, key: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self._client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            raise


def get_storage_backend() -> StorageBackend:
    """Factory function to get the appropriate storage backend.

    Returns:
        S3StorageBackend if S3_BUCKET_NAME is set, otherwise LocalStorageBackend.
    """
    if os.environ.get("S3_BUCKET_NAME"):
        return S3StorageBackend()
    return LocalStorageBackend()
