"""Storage abstraction package with support for local and S3 backends."""

from packages.storage.client import (
    LocalStorageBackend,
    S3StorageBackend,
    StorageBackend,
    get_storage_backend,
)

__all__ = [
    "StorageBackend",
    "LocalStorageBackend",
    "S3StorageBackend",
    "get_storage_backend",
]
