# -*- coding:utf-8 -*-
from abc import ABC, abstractmethod
from io import BytesIO


class StorageBackend(ABC):

    @abstractmethod
    def upload(self, file_data: bytes, file_path: str, mime_type: str = 'application/octet-stream') -> dict:
        """Upload a file.

        Returns:
            dict: {"stored_path": str, "size": int}
        """
        ...

    @abstractmethod
    def download(self, stored_path: str) -> tuple:
        """Download a file.

        Returns:
            tuple: (BytesIO_stream, filename, mime_type)
        """
        ...

    @abstractmethod
    def delete(self, stored_path: str) -> bool:
        """Delete a file. Returns True if deleted, False if not found."""
        ...

    @abstractmethod
    def get_url(self, stored_path: str, expires: int = 3600) -> str:
        """Get a direct access URL for the file."""
        ...
